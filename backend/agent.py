import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from memory import save_message, get_recent_history
from rag import retrieve_context
from tools import TOOL_SCHEMAS, dispatch_tool

load_dotenv(override=True)

# Gemini via OpenAI-compatible endpoint (proven pattern from the course)
_client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOOL_ROUNDS = 5

# ── Load knowledge base once at startup ──────────────────────────────────────

def _load_knowledge_base() -> str:
    kb_dir = Path(__file__).parent / "knowledge_base"
    texts = []
    for md_file in sorted(kb_dir.glob("*.md")):
        texts.append(f"## {md_file.stem.upper()}\n{md_file.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(texts)


_STATIC_PROFILE = _load_knowledge_base()

# ── OpenAI function-call tool format ─────────────────────────────────────────

_TOOLS = [{"type": "function", "function": schema} for schema in TOOL_SCHEMAS]


# ── System prompt ─────────────────────────────────────────────────────────────

def _build_system_prompt(rag_chunks: list[str]) -> str:
    rag_section = ""
    if rag_chunks:
        joined = "\n\n".join(f"[Excerpt {i+1}]\n{c}" for i, c in enumerate(rag_chunks))
        rag_section = f"\n\n## MOST RELEVANT CONTEXT FOR THIS QUESTION\n{joined}"

    return (
        "You are acting as Ibryam Faik, a Senior Data Analyst and Data Engineer. "
        "You are answering questions on Ibryam's personal portfolio website (ibryam.com). "
        "Visitors are typically HR recruiters, hiring managers, or data professionals "
        "who want to learn about his background, skills, projects, and career goals.\n\n"
        "Your responsibilities:\n"
        "- Answer all questions about Ibryam's career, technical skills, projects, and background "
        "faithfully and accurately using the profile data below.\n"
        "- Be professional, warm, and engaging — you are speaking on his behalf.\n"
        "- If a recruiter shares their email or expresses interest in contact, use record_user_details.\n"
        "- If you cannot answer a question from the provided profile, use record_unknown_question "
        "AND tell the user you'll pass it to Ibryam directly.\n"
        "- Use faq_lookup for questions about salary, notice period, availability, relocation, "
        "or anything that may have a prepared answer.\n"
        "- Keep responses concise (3-5 sentences) unless detail is clearly needed.\n"
        "- Never invent facts not present in the profile data.\n\n"
        f"## IBRYAM'S FULL PROFILE\n{_STATIC_PROFILE}"
        f"{rag_section}"
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

    except RateLimitError:
        return "I'm temporarily busy — please try again in a moment."

    return "I ran into an issue generating a response. Please try again."
