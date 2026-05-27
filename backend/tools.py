import json
import os
import requests
from dotenv import load_dotenv
from memory import save_lead, search_faq, get_recent_history, save_unknown_question

load_dotenv(override=True)

_TELEGRAM_API = "https://api.telegram.org/bot"


# ── Telegram ──────────────────────────────────────────────────────────────────

def _telegram(title: str, message: str) -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[telegram] disabled — {title}: {message}")
        return
    text = f"<b>{title}</b>\n{message}"
    for attempt in range(2):
        try:
            r = requests.post(
                url=f"{_TELEGRAM_API}{token}/sendMessage",
                params={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"},
                timeout=15,
            )
            if r.ok:
                print(f"[telegram] sent — {title}")
                return
            else:
                print(f"[telegram] FAILED {r.status_code}: {r.text}")
                return
        except Exception as e:
            print(f"[telegram] error attempt {attempt + 1}: {e}")
    print(f"[telegram] gave up after 2 attempts — {title}")


# ── Tool functions ────────────────────────────────────────────────────────────

def record_user_details(email: str, name: str = "not provided", notes: str = "not provided", session_id: str = "") -> dict:
    print(f"[tool] record_user_details — name={name} email={email}")
    save_lead(session_id=session_id, email=email, name=name, notes=notes)
    _telegram(
        "ibryam.com — New Contact",
        f"Name: {name}\nEmail: {email}\nNotes: {notes}",
    )
    return {"recorded": True, "message": "Thank you, Ibryam will be in touch soon."}


def record_unknown_question(question: str, session_id: str = "") -> dict:
    print(f"[tool] record_unknown_question — {question[:80]}")
    save_unknown_question(question=question, session_id=session_id)
    _telegram("ibryam.com — Unknown Question", question)
    return {"recorded": True}


def faq_lookup(query: str) -> dict:
    results = search_faq(query, limit=3)
    if not results:
        return {"found": False, "results": []}
    return {"found": True, "results": results}


def get_session_context(session_id: str) -> dict:
    history = get_recent_history(session_id, limit=10)
    if not history:
        return {"history": []}
    return {"history": history}


# ── JSON schemas for the Gemini function-calling API ─────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "record_user_details",
        "description": (
            "Use this tool when a recruiter or visitor provides their email address "
            "and wants to be contacted by Ibryam. Record their name, email, and any notes "
            "about the conversation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The visitor's email address"},
                "name": {"type": "string", "description": "The visitor's name if provided"},
                "notes": {"type": "string", "description": "Key points from the conversation worth noting"},
                "session_id": {"type": "string", "description": "The current session identifier"},
            },
            "required": ["email"],
        },
    },
    {
        "name": "record_unknown_question",
        "description": (
            "Always use this tool when you cannot answer a question because the information "
            "is not available in the provided profile or context. This notifies Ibryam so he "
            "can follow up or improve the knowledge base."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question that could not be answered"},
                "session_id": {"type": "string", "description": "The current session identifier"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "faq_lookup",
        "description": (
            "Search the FAQ database for answers to common recruiter and HR questions about Ibryam. "
            "Use this before answering questions about salary, notice period, availability, or anything "
            "that might have a prepared answer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or topic to search for in the FAQ"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_session_context",
        "description": (
            "Retrieve recent conversation history for this session. Use this when the user refers "
            "to something discussed earlier in the conversation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The current session identifier"},
            },
            "required": ["session_id"],
        },
    },
]


TOOL_REGISTRY = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
    "faq_lookup": faq_lookup,
    "get_session_context": get_session_context,
}


def dispatch_tool(name: str, args: dict) -> str:
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**args)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})
