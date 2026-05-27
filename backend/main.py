import uuid
from contextlib import asynccontextmanager

import requests as http_requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=True)

from agent import chat as agent_chat
from evaluator import evaluate
from memory import init_db, get_unknown_questions, mark_question_answered, save_visit, was_ip_seen_recently, get_daily_stats
from rag import init_rag
from tools import _telegram


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] initialising database…")
    init_db()
    print("[startup] initialising RAG vector store…")
    init_rag()
    print("[startup] ready.")
    yield


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
async def record_visit(request: Request, body: dict = {}):
    session_id = body.get("session_id", "")
    ip = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )

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
    _telegram("ibryam.com — New Visitor", f"Location: {location}\nSession: {session_id[:8]}…")
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


@app.get("/admin/unknown-questions")
async def unknown_questions(unanswered_only: bool = True):
    return {"questions": get_unknown_questions(unanswered_only=unanswered_only)}


@app.post("/admin/unknown-questions/{question_id}/answered")
async def mark_answered(question_id: int):
    mark_question_answered(question_id)
    return {"marked": True, "id": question_id}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())

    reply = agent_chat(
        message=req.message,
        session_id=session_id,
        history=req.history,
    )

    # Evaluate in background for logging — never blocks or retries (saves API quota)
    from rag import retrieve_context
    rag_chunks = retrieve_context(req.message)
    verdict = evaluate(req.message, rag_chunks, reply)
    if verdict["decision"] == "REJECTED":
        print(f"[eval] REJECTED ({verdict['confidence']}%) — {verdict['reason']}")

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        eval_decision=verdict["decision"],
        eval_confidence=verdict["confidence"],
    )
