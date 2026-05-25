import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=True)

from agent import chat as agent_chat
from evaluator import evaluate
from memory import init_db, get_recent_history
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


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())

    # Retrieve RAG context for the evaluator (agent does its own retrieval internally)
    from rag import retrieve_context
    rag_chunks = retrieve_context(req.message)

    # First attempt
    reply = agent_chat(
        message=req.message,
        session_id=session_id,
        history=req.history,
    )

    # Evaluate the response
    verdict = evaluate(req.message, rag_chunks, reply)

    # If rejected, try once more with a hint
    if verdict["decision"] == "REJECTED":
        print(f"[eval] REJECTED ({verdict['confidence']}%) — {verdict['reason']} — retrying")
        hint_history = get_recent_history(session_id, limit=8)
        hint_history.append({
            "role": "user",
            "content": (
                f"[INTERNAL NOTE: Your previous response was flagged as inaccurate by "
                f"the quality evaluator: {verdict['reason']}. "
                f"Please answer again more carefully, sticking strictly to the profile data.]"
            ),
        })
        reply = agent_chat(
            message=req.message,
            session_id=session_id,
            history=hint_history,
        )
        verdict = evaluate(req.message, rag_chunks, reply)

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        eval_decision=verdict["decision"],
        eval_confidence=verdict["confidence"],
    )
