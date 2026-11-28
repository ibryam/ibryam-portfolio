import asyncio
import time
import uuid
from contextlib import asynccontextmanager

import requests as http_requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=True)

from agent import chat as agent_chat
from evaluator import evaluate
from memory import (
    init_db, get_unknown_questions, mark_question_answered, save_visit, was_ip_seen_recently, get_daily_stats,
    get_conversation, get_session_lead, count_session_unknown_questions, get_location_for_ip,
)
from rag import init_rag
from tools import _telegram, _notify


# ── Conversation summaries: one Telegram message per conversation, sent once it goes quiet ──

_SUMMARY_IDLE_SECONDS = 180
_SUMMARY_ANSWER_CHARS = 400
_active_sessions: dict[str, tuple[float, str]] = {}  # session_id -> (last activity, client ip)
_reported_counts: dict[str, int] = {}  # session_id -> messages already sent in a summary


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _format_transcript(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        if m["role"] == "user":
            lines.append(f"\n🧑 {m['content']}")
        else:
            answer = m["content"]
            if len(answer) > _SUMMARY_ANSWER_CHARS:
                answer = answer[:_SUMMARY_ANSWER_CHARS] + "…"
            lines.append(f"🤖 {answer}")
    return "\n".join(lines)


def _send_summary(session_id: str, ip: str, send=_notify) -> None:
    messages = get_conversation(session_id)
    already_sent = _reported_counts.get(session_id, 0)
    new_messages = messages[already_sent:]
    if not new_messages:
        return
    _reported_counts[session_id] = len(messages)

    lead = get_session_lead(session_id)
    contact = f"{lead['name']} <{lead['email']}>" if lead else "no email left"
    questions = sum(1 for m in new_messages if m["role"] == "user")
    title = "ibryam.com — Conversation" + (" (continued)" if already_sent else "")
    header = (
        f"📍 {get_location_for_ip(ip)}\n"
        f"📧 {contact}\n"
        f"💬 {questions} question(s), {count_session_unknown_questions(session_id)} unknown\n"
        f"Session: {session_id[:8]}"
    )
    send(title, header + "\n" + _format_transcript(new_messages))


async def _summary_loop() -> None:
    while True:
        await asyncio.sleep(30)
        now = time.monotonic()
        idle = [sid for sid, (ts, _) in _active_sessions.items() if now - ts >= _SUMMARY_IDLE_SECONDS]
        for sid in idle:
            _, ip = _active_sessions.pop(sid)
            try:
                await asyncio.to_thread(_send_summary, sid, ip)
            except Exception as e:
                print(f"[summary] failed for {sid[:8]}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] initialising database…")
    init_db()
    print("[startup] initialising RAG vector store…")
    init_rag()
    print("[startup] warming up embedding model…")
    from rag import retrieve_context
    retrieve_context("data engineer experience skills")
    print("[startup] ready.")
    summary_task = asyncio.create_task(_summary_loop())
    yield
    summary_task.cancel()
    _flush_summaries()


def _flush_summaries() -> None:
    # HF Spaces restarts start from a fresh disk, so pending summaries can't be persisted —
    # send them synchronously on shutdown instead (the queue worker thread may not drain in time).
    for sid, (_, ip) in list(_active_sessions.items()):
        try:
            _send_summary(sid, ip, send=_telegram)
        except Exception as e:
            print(f"[summary] shutdown flush failed for {sid[:8]}: {e}")
    _active_sessions.clear()


app = FastAPI(title="Ibryam AI Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ibryam.com",
        "https://www.ibryam.com",
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:5500",  # VS Code Live Server
        "null",                   # local file:// opens
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    history: list[dict] | None = None  # optional in-memory history override


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    eval_decision: str = "APPROVED"
    eval_confidence: int = 100


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/visit")
async def record_visit(request: Request, background_tasks: BackgroundTasks, body: dict = {}):
    session_id = body.get("session_id", "")
    ip = _client_ip(request)

    if was_ip_seen_recently(ip, minutes=60):
        return {"status": "already_seen"}

    country, region, city = "Unknown", "", ""
    try:
        geo = http_requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city", timeout=4).json()
        if geo.get("status") == "success":
            country = geo.get("country", "Unknown")
            region = geo.get("regionName", "")
            city = geo.get("city", "")
    except Exception as e:
        print(f"[visit] geo lookup failed: {e}")

    save_visit(session_id=session_id, ip=ip, country=country, region=region, city=city)

    location = ", ".join(filter(None, [city, region, country]))
    background_tasks.add_task(_telegram, "ibryam.com — New Visitor", f"Location: {location}\nSession: {session_id[:8]}…")
    print(f"[visit] {ip} — {location}")
    return {"status": "recorded"}


@app.get("/admin/daily-report")
async def daily_report(send_telegram: bool = False):
    stats = get_daily_stats()
    if send_telegram:
        countries_txt = "\n".join(f"  {c}: {n}" for c, n in sorted(stats["countries"].items(), key=lambda x: -x[1])) or "  none"
        unknowns_txt = "\n".join(f"  • {q[:80]}" for q in stats["unknown_questions"][:5]) or "  none"
        leads_txt = "\n".join(f"  {l['name']} — {l['email']}" for l in stats["new_leads"]) or "  none"
        msg = (
            f"Visits: {stats['visit_count']}\n"
            f"Countries:\n{countries_txt}\n"
            f"Questions asked: {stats['question_count']}\n"
            f"Unknown questions: {stats['unknown_count']}\n{unknowns_txt}\n"
            f"New leads: {len(stats['new_leads'])}\n{leads_txt}"
        )
        _telegram("ibryam.com — Daily Report", msg)
    return stats


@app.get("/admin/test-telegram")
async def test_telegram():
    import os
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return {"token_set": bool(token), "chat_id_set": bool(chat_id), "error": "credentials missing in env"}
    _telegram("ibryam.com — HF Space Test", "Synchronous test from HF Space backend.")
    return {"token_set": True, "chat_id_set": True, "token_prefix": token[:8], "chat_id": chat_id}


@app.get("/admin/unknown-questions")
async def unknown_questions(unanswered_only: bool = True):
    return {"questions": get_unknown_questions(unanswered_only=unanswered_only)}


@app.post("/admin/unknown-questions/{question_id}/answered")
async def mark_answered(question_id: int):
    mark_question_answered(question_id)
    return {"marked": True, "id": question_id}


def _run_evaluator(message: str, rag_chunks: list, reply: str) -> None:
    verdict = evaluate(message, rag_chunks, reply)
    if verdict["decision"] == "REJECTED":
        print(f"[eval] REJECTED ({verdict['confidence']}%) — {verdict['reason']}")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, background_tasks: BackgroundTasks):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())

    reply, rag_chunks = agent_chat(
        message=req.message,
        session_id=session_id,
        history=req.history,
    )

    _active_sessions[session_id] = (time.monotonic(), _client_ip(request))

    # Evaluator runs after response is returned — zero added latency
    background_tasks.add_task(_run_evaluator, req.message, rag_chunks, reply)

    return ChatResponse(reply=reply, session_id=session_id)
