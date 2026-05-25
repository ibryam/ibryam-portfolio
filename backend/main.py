import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=True)

from agent import chat as agent_chat
from evaluator import evaluate
from memory import init_db, get_unknown_questions, mark_question_answered
from rag import init_rag


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
