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

_TOOLS = [{"type": "function", "function": schema} for schema in TOOL_SCHEMAS]


# ── Load profile once at startup ──────────────────────────────────────────────

def _load_profile() -> str:
    profile_path = Path(__file__).parent / "knowledge_base" / "profile.md"
    return profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""


_PROFILE = _load_profile()


# ── System prompt ─────────────────────────────────────────────────────────────

def _build_system_prompt(rag_chunks: list[str]) -> str:
    context = ""
    if rag_chunks:
        joined = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(rag_chunks))
        context = f"\n\n## RELEVANT CONTEXT FOR THIS QUESTION\n{joined}"

    return (
        "You are acting as Ibryam Faik on his personal portfolio website ibryam.com. "
        "Visitors are HR recruiters, hiring managers, and data professionals.\n\n"
        "IMPORTANT TOOL RULES — follow these before responding:\n"
        "1. Questions about notice period, salary, availability, relocation, or start date: "
        "you MUST call faq_lookup before answering. Do not guess — look it up first.\n"
        "2. Visitor shares an email address: you MUST call record_user_details immediately.\n"
        "3. You cannot answer from the profile data: you MUST call record_unknown_question, "
        "then tell the visitor Ibryam will follow up. Never make up facts.\n"
        "4. Keep answers concise (3-5 sentences). Be professional and warm.\n\n"
        f"## IBRYAM'S PROFILE\n{_PROFILE}"
        f"{context}"
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
                    if tc.function.name in ("record_user_details", "get_session_context"):
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
