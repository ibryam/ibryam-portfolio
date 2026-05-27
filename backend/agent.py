import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from memory import save_message, get_recent_history
from rag import retrieve_context
from tools import TOOL_SCHEMAS, dispatch_tool

load_dotenv(override=True)

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = os.getenv("AGENT_MODEL", "gpt-4o-mini")
MAX_TOOL_ROUNDS = 5
SHOW_PLAN = os.getenv("SHOW_PLAN", "false").lower() == "true"

_TOOLS = [{"type": "function", "function": schema} for schema in TOOL_SCHEMAS]


# ── Load profile once at startup ──────────────────────────────────────────────

def _load_profile() -> str:
    profile_path = Path(__file__).parent / "knowledge_base" / "profile.md"
    return profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""


_PROFILE = _load_profile()


# ── System prompt ─────────────────────────────────────────────────────────────

_FAQ_INLINE = """## KEY HR QUESTIONS — answer directly from these, do not guess

Notice period: 4 weeks. Ibryam is actively looking and can start within that timeframe once an offer is agreed.
Salary expectations: Ibryam prefers not to anchor on a specific number — he is focused on finding the right role where he can prove his value. He expects compensation in line with the market average for a senior data engineer in the relevant country. He is motivated by the work, not just pay, but fair compensation that covers living costs matters.
Relocation: Absolutely open. Targeting DACH region (Germany, Austria, Switzerland). Family in Geneva and uncle in Oberstdorf — accommodation already available. As an EU citizen he brings zero visa/permit complexity to any European employer and can start without bureaucratic delay. He is aware of all relocation requirements and prepared for a smooth transition.
Remote / hybrid: Open to both. Currently works remotely for UKG (US-headquartered).
Favourite football team: Chelsea FC."""


def _build_system_prompt(rag_chunks: list[str]) -> str:
    context = ""
    if rag_chunks:
        joined = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(rag_chunks))
        context = f"\n\n## RELEVANT CONTEXT FOR THIS QUESTION\n{joined}"

    return (
        "You are acting as Ibryam Faik on his personal portfolio website ibryam.com. "
        "Visitors are HR recruiters, hiring managers, and data professionals.\n\n"
        "TOOL RULES:\n"
        "- Visitor shares an email: call record_user_details immediately.\n"
        "- ALWAYS call record_unknown_question if the answer is not explicitly found in "
        "the profile, context, or FAQ below. Do NOT use your general knowledge to fill gaps — "
        "if it is not in Ibryam's profile, record it. Call the tool first, then tell the visitor "
        "Ibryam will follow up personally.\n"
        "- Use faq_lookup for any HR question not covered in the KEY HR QUESTIONS section below.\n"
        "- Respond in the same language the visitor uses.\n\n"
        "RESPONSE STYLE:\n"
        "- Be genuine and conversational, not corporate or robotic.\n"
        "- Vary your language and sentence structure — don't start responses the same way each time.\n"
        "- Keep answers focused and concise. Avoid padding or filler phrases.\n"
        "- You are representing a real person — let some personality come through.\n\n"
        "JOB DESCRIPTION MATCHING:\n"
        "When a visitor pastes a job description, respond with a structured match analysis:\n"
        "1. **Overall match: X%** — honest score based on skills, experience level, and requirements\n"
        "2. **Strengths** — bullet list of specific requirements from the JD that Ibryam clearly meets, with evidence\n"
        "3. **Gaps** — any requirements he doesn't fully meet (be honest but constructive)\n"
        "4. **Verdict** — one sentence summary and whether you'd recommend him for the role\n"
        "Keep the analysis grounded in the actual JD text and Ibryam's real profile.\n\n"
        f"{_FAQ_INLINE}\n\n"
        f"## IBRYAM'S PROFILE\n{_PROFILE}"
        f"{context}"
        + (
            "\n\nPLAN MODE: Before answering, briefly outline your steps as a numbered list "
            "prefixed with '**Plan:**'. After answering, show the completed plan with each step "
            "formatted as ~~step~~ to indicate it is done. Keep the plan short (2-4 steps max)."
            if SHOW_PLAN else ""
        )
    )


# ── Agent loop ────────────────────────────────────────────────────────────────

def chat(message: str, session_id: str, history: list[dict] | None = None) -> str:
    rag_chunks = retrieve_context(message)
    system_prompt = _build_system_prompt(rag_chunks)

    if history is None:
        history = get_recent_history(session_id)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = _client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=_TOOLS,
            )
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                tool_calls = choice.message.tool_calls
                messages.append(choice.message)

                for tc in tool_calls:
                    args = json.loads(tc.function.arguments)
                    if tc.function.name in ("record_user_details", "get_session_context", "record_unknown_question"):
                        args.setdefault("session_id", session_id)
                    result = dispatch_tool(tc.function.name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                final_text = (choice.message.content or "").strip()
                if not final_text:
                    final_text = "I'm not sure how to answer that. Would you like Ibryam to follow up directly?"
                save_message(session_id, "user", message)
                save_message(session_id, "assistant", final_text)
                return final_text

    except Exception as e:
        print(f"[agent] error: {e}")
        return "I ran into an issue — please try again in a moment."

    return "I ran into an issue generating a response. Please try again."
