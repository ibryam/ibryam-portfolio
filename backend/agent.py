import json
import os
from pathlib import Path

from dotenv import load_dotenv
import anthropic

from memory import save_message, get_recent_history
from rag import retrieve_context
from tools import TOOL_SCHEMAS, dispatch_tool

load_dotenv(override=True)

_client = anthropic.Anthropic()

MODEL = os.getenv("AGENT_MODEL", "claude-sonnet-5")
MAX_TOOL_ROUNDS = 5
SHOW_PLAN = os.getenv("SHOW_PLAN", "false").lower() == "true"

_TOOLS = [
    {"name": s["name"], "description": s["description"], "input_schema": s["parameters"]}
    for s in TOOL_SCHEMAS
]


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


def _build_static_prompt() -> str:
    return (
        "You are Ibryam Faik's AI assistant on his portfolio website ibryam.com. "
        "Visitors are mostly HR recruiters and hiring managers deciding whether to contact him, "
        "so every answer should help them judge his fit quickly. Refer to Ibryam in the third "
        "person (\"he\", \"Ibryam\") — the chat widget introduces you as his assistant.\n\n"
        "WHAT YOU KNOW:\n"
        "Your only source of facts about Ibryam is his profile, the key HR answers, the relevant "
        "context section (when present), and faq_lookup results. If the answer isn't in any of "
        "those, don't guess or fill in plausible details — call record_unknown_question and tell "
        "the visitor Ibryam will follow up personally. Inventing a skill or date would mislead a "
        "recruiter, which is worse than saying you don't know.\n\n"
        "TOOLS:\n"
        "- When a visitor shares an email address, call record_user_details.\n"
        "- For HR questions not covered by the key HR answers below, check faq_lookup before answering.\n\n"
        "RESPONSE STYLE:\n"
        "- Reply in the visitor's language.\n"
        "- Lead with the direct answer, then add one or two concrete specifics from the profile "
        "(a project, tool, or result) that back it up.\n"
        "- Simple questions get 2–4 sentences. Go longer only for job description analyses or "
        "when the visitor asks for detail.\n"
        "- Be warm and conversational, like a colleague who knows Ibryam well — not a sales pitch. "
        "Vary how you open your replies.\n"
        "- When it fits naturally (e.g. after a strong match or a question about availability), "
        "invite the visitor to leave their email so Ibryam can reach out. Don't ask every turn.\n"
        "- The chat window renders only **bold** text and line breaks. Don't use headings, tables, "
        "links in markdown syntax, or italics; for lists, put each item on its own line starting with \"• \".\n\n"
        "JOB DESCRIPTION MATCHING:\n"
        "When a visitor pastes a job description, respond with a structured match analysis:\n"
        "1. **Overall match: X%** — honest score based on skills, experience level, and requirements\n"
        "2. **Strengths** — bullet list of specific requirements from the JD that Ibryam clearly meets, with evidence\n"
        "3. **Gaps** — any requirements he doesn't fully meet (be honest but constructive)\n"
        "4. **Verdict** — one sentence summary and whether you'd recommend him for the role\n"
        "Keep the analysis grounded in the actual JD text and Ibryam's real profile.\n\n"
        f"{_FAQ_INLINE}\n\n"
        f"## IBRYAM'S PROFILE\n{_PROFILE}"
        + (
            "\n\nPLAN MODE: Before answering, briefly outline your steps as a numbered list "
            "prefixed with '**Plan:**'. After answering, show the completed plan with each step "
            "formatted as ~~step~~ to indicate it is done. Keep the plan short (2-4 steps max)."
            if SHOW_PLAN else ""
        )
    )


_STATIC_PROMPT = _build_static_prompt()


def _build_system_prompt(rag_chunks: list[str]) -> list[dict]:
    blocks = [{"type": "text", "text": _STATIC_PROMPT, "cache_control": {"type": "ephemeral"}}]
    if rag_chunks:
        joined = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(rag_chunks))
        blocks.append({"type": "text", "text": f"## RELEVANT CONTEXT FOR THIS QUESTION\n{joined}"})
    return blocks


# ── Agent loop ────────────────────────────────────────────────────────────────

_UNCERTAINTY = [
    "not mentioned", "isn't mentioned", "not in his profile", "not available in",
    "i don't have", "i do not have", "no information", "not provided", "cannot find",
    "not specified", "doesn't include", "does not include", "i'm not sure", "i am not sure",
    "don't have access", "do not have access", "not in the profile", "not included in",
    "no details", "doesn't contain", "does not contain", "not covered", "isn't covered",
    "no mention", "isn't listed", "is not listed", "not share", "hasn't shared",
    "that information", "this information", "unavailable", "not disclosed",
]


def chat(message: str, session_id: str, history: list[dict] | None = None) -> tuple[str, list]:
    rag_chunks = retrieve_context(message)
    system_prompt = _build_system_prompt(rag_chunks)

    if history is None:
        history = get_recent_history(session_id)

    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        unknown_recorded = False

        for _ in range(MAX_TOOL_ROUNDS):
            response = _client.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=system_prompt,
                messages=messages,
                tools=_TOOLS,
                output_config={"effort": "medium"},
            )

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    args = dict(block.input)
                    if block.name in ("record_user_details", "get_session_context", "record_unknown_question"):
                        args.setdefault("session_id", session_id)
                    if block.name == "record_unknown_question":
                        unknown_recorded = True
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": dispatch_tool(block.name, args),
                    })
                messages.append({"role": "user", "content": tool_results})
            else:
                final_text = "".join(b.text for b in response.content if b.type == "text").strip()
                if not final_text:
                    final_text = "I'm not sure how to answer that. Would you like Ibryam to follow up directly?"

                # Auto-flag if agent said it doesn't know but didn't call the tool
                response_signals_unknown = any(p in final_text.lower() for p in _UNCERTAINTY)
                if not unknown_recorded and response_signals_unknown:
                    print(f"[agent] auto-flagging unknown question: {message[:80]}")
                    dispatch_tool("record_unknown_question", {"question": message, "session_id": session_id})

                save_message(session_id, "user", message)
                save_message(session_id, "assistant", final_text)
                return final_text, rag_chunks

    except Exception as e:
        print(f"[agent] error: {e}")
        return "I ran into an issue — please try again in a moment.", rag_chunks

    return "I ran into an issue generating a response. Please try again.", rag_chunks
