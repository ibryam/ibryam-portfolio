# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

**Name:** ibryam-portfolio
**Purpose:** Personal portfolio site at ibryam.com + AI career chatbot that acts as Ibryam Faik's representative to HR recruiters
**Stack:** Python · FastAPI · Gemini 2.5 Flash · Groq (llama-3.3-70b) · ChromaDB · SQLite · Vanilla HTML/CSS/JS · HuggingFace Spaces · Cloudflare Pages

## Quick Start

```powershell
# Backend — from D:\00.Projects\ibryam-portfolio\backend\
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt

# Copy and fill in API keys
cp .env.example .env

# Run locally (auto-inits DB + RAG on first run)
uvicorn main:app --reload --port 8000

# Frontend — open in browser directly or via Live Server
# frontend/index.html — set BACKEND_URL to http://localhost:8000
```

## Architecture

```
Recruiter → Custom chat widget (frontend/index.html)
                │ POST /chat
                ▼
          FastAPI (backend/main.py)
                │
          ┌─────┴──────┐
     agent.py          evaluator.py
   (Gemini 2.5 Flash)  (Groq llama-3.3-70b)
          │                    │
    ┌─────┴─────┐         APPROVED/REJECTED
   rag.py    tools.py     (retry on reject)
  (ChromaDB)  (4 tools)
          │
      memory.py (SQLite)
```

**Agent tools (tools.py):**
- `record_user_details` — saves lead to SQLite + Pushover notification
- `record_unknown_question` — Pushover alert for unanswerable questions
- `faq_lookup` — FTS5 full-text search over 30 curated Q&A pairs
- `get_session_context` — retrieves recent conversation history from SQLite

**RAG flow:** On each chat request, `rag.py` retrieves top-5 ChromaDB chunks (score ≥ 0.25) from knowledge_base/ + LinkedIn PDF. Chunks are injected into Gemini's system prompt as extra context.

**Evaluator flow:** After agent response, Groq evaluates APPROVED/REJECTED. On rejection, agent is called again with a hint. Always returns a response (fail-open).

## Environment Variables

```
GOOGLE_API_KEY     — Google AI Studio key (gemini-2.5-flash, free tier)
GROQ_API_KEY       — Groq key (llama-3.3-70b-versatile evaluator, free tier)
PUSHOVER_TOKEN     — Pushover app token (agentic notifications)
PUSHOVER_USER      — Pushover user key
BACKEND_URL        — Full URL of deployed backend (set in frontend JS)
GEMINI_MODEL       — Override Gemini model (default: gemini-2.5-flash)
GROQ_MODEL         — Override Groq model (default: llama-3.3-70b-versatile)
DB_PATH            — SQLite file path (default: ibryam_chat.db)
KB_DIR             — Knowledge base directory (default: ./knowledge_base)
VECTOR_STORE_DIR   — ChromaDB persist dir (default: ./vector_store)
LINKEDIN_PDF       — Path to LinkedIn PDF (default: ./me/linkedin.pdf)
```

Copy `.env.example` → `.env` before running locally.

## File Structure

```
backend/
  main.py          — FastAPI app, startup lifecycle, /chat orchestration
  agent.py         — Gemini agent loop, system prompt, tool dispatch
  evaluator.py     — Groq evaluator (APPROVED/REJECTED)
  rag.py           — ChromaDB init, ingest, retrieve_context()
  memory.py        — SQLite: conversations, FAQ FTS5, leads
  tools.py         — Tool functions + Gemini function-call schemas
  knowledge_base/  — profile.md, projects.md, experience.md, faq.md
  me/              — linkedin.pdf (gitignored)
  vector_store/    — ChromaDB data (gitignored)
  Dockerfile       — for HuggingFace Spaces deployment
frontend/
  index.html       — Portfolio + floating chat widget
```

## Non-obvious Patterns

- **RAG is injected twice:** `agent.py` calls `retrieve_context()` for the system prompt; `main.py` also calls it for the evaluator. This is intentional — both need the same context but use it differently.
- **Gemini function-calling format:** Uses `genai.protos.FunctionDeclaration` / `genai.protos.Tool` — NOT the OpenAI format. Don't mix patterns.
- **Fail-open evaluator:** `evaluator.py` returns APPROVED on any exception — never block the user due to Groq being unavailable.
- **SQLite thread safety:** `get_connection()` uses `check_same_thread=False` because FastAPI runs in async context. This is safe for read-heavy workloads; don't do long write transactions.
- **Vector store init:** First run downloads ~90MB sentence-transformers model. On HF Spaces this happens once at container startup. Subsequent runs load from cache.
- **CORS:** `"null"` is included in allow_origins to support local `file://` testing of index.html.
- **faq_lookup FTS5:** SQLite FTS5 uses simple tokenizer. Queries with special characters need escaping — the current `search_faq()` passes query directly; avoid quotes in queries.

## Deployment

**Backend → HuggingFace Spaces (Docker):**
- Create Space: type=Docker, visibility=Public
- Push `backend/` contents to Space repo
- Add secrets: GOOGLE_API_KEY, GROQ_API_KEY, PUSHOVER_TOKEN, PUSHOVER_USER
- Space URL: `https://ibryam-chatbot.hf.space`

**Frontend → Cloudflare Pages:**
- Connect GitHub repo → Pages project → build: none (static HTML)
- Custom domain: ibryam.com (Cloudflare DNS auto-configured)
- Set `BACKEND_URL` constant in `frontend/index.html` to HF Space URL

## Rules

- Code style → `.claude/rules/code-style.md`
- Testing → `.claude/rules/testing.md`
- API conventions → `.claude/rules/api-conventions.md`

## Commands

- `/review` — full review of staged changes (correctness, security, style)
- `/fix-issue <description>` — autonomous bug fix from a plain-language description

## Agents

- `code-reviewer` — correctness, performance, style (see `.claude/agents/code-reviewer.md`)
- `security-auditor` — OWASP, secrets, auth, injection (see `.claude/agents/security-auditor.md`)
