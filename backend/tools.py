import json
import os
import requests
from dotenv import load_dotenv
from memory import save_lead, search_faq, get_recent_history

load_dotenv(override=True)


# ── Pushover ─────────────────────────────────────────────────────────────────

def _pushover(title: str, message: str) -> None:
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print(f"[pushover] disabled — {title}: {message}")
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "title": title, "message": message},
            timeout=8,
        )
    except Exception as e:
        print(f"[pushover] error: {e}")


# ── Tool functions ────────────────────────────────────────────────────────────

def record_user_details(email: str, name: str = "not provided", notes: str = "not provided", session_id: str = "") -> dict:
    save_lead(session_id=session_id, email=email, name=name, notes=notes)
    _pushover(
        "ibryam.com — New Contact",
        f"Name: {name}\nEmail: {email}\nNotes: {notes}",
    )
    return {"recorded": True, "message": "Thank you, Ibryam will be in touch soon."}


def record_unknown_question(question: str) -> dict:
    _pushover("ibryam.com — Unknown Question", question)
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
