# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

**Name:** ibryam-portfolio
**Purpose:** Personal portfolio site at ibryam.com + AI career chatbot that acts as Ibryam Faik's assistant for HR recruiters
**Stack:** Python · FastAPI · Claude Sonnet 5 (Anthropic SDK) · Gemini/Groq evaluator · ChromaDB · SQLite · Telegram · Vanilla HTML/CSS/JS · HuggingFace Spaces · Cloudflare Pages

## Quick Start

```powershell
# Backend — from D:\00.Projects\ibryam-portfolio\backend\
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt

# Create backend/.env with the keys listed below

# Run locally (auto-inits DB + RAG on first run)
uvicorn main:app --reload --port 8000

# Frontend — open in browser directly or via Live Server
# frontend/index.html — set BACKEND_URL to http://localhost:8000
```

## Architecture

```
Recruiter → Custom chat widget (frontend/index.html)
                │ POST /visit (on chat open), POST /chat
                ▼
          FastAPI (backend/main.py) ── idle-conversation summary loop → Telegram
                │
          ┌─────┴──────────────┐
     agent.py              evaluator.py (background, log-only)
   (Claude Sonnet 5)       (Gemini → Groq fallback)
          │
    ┌─────┴─────┐
   rag.py    tools.py ── instant Telegram alerts (new contact, unknown question)
  (ChromaDB)  (4 tools)
          │
      memory.py (SQLite)
```

**Agent tools (tools.py):**
- `record_user_details` — saves lead to SQLite + Telegram alert
- `record_unknown_question` — saves to SQLite + Telegram alert
- `faq_lookup` — FTS5 full-text search over curated Q&A (seeded from knowledge_base/faq.md)
- `get_session_context` — retrieves recent conversation history from SQLite

**RAG flow:** `rag.py` retrieves top-5 ChromaDB chunks (score ≥ 0.25) from knowledge_base/ + LinkedIn PDF. They are sent as a second system block after the cached static prompt (profile + instructions).

**Evaluator flow:** Runs as a FastAPI background task after the response is returned; REJECTED verdicts are only logged. Fail-open.

**Telegram flow:** `main.py` tracks active sessions in memory; after 3 min idle it sends one summary per conversation (location, contact, full Q&A). Returning visitors get a "(continued)" message with only new messages.

## Environment Variables

```
ANTHROPIC_API_KEY  — Claude API key (agent)
AGENT_MODEL        — Override agent model (default: claude-sonnet-5)
GOOGLE_API_KEY     — Gemini key for the evaluator
GROQ_API_KEY       — Groq key, evaluator fallback
GEMINI_EVAL_MODEL  — default: gemini-2.0-flash
GROQ_EVAL_MODEL    — default: llama-3.1-8b-instant
TELEGRAM_TOKEN     — Telegram bot token
TELEGRAM_CHAT_ID   — Telegram chat that receives notifications
SHOW_PLAN          — "true" adds a visible plan to replies (default: false)
DB_PATH            — SQLite file path (default: ibryam_chat.db)
KB_DIR             — Knowledge base directory (default: ./knowledge_base)
VECTOR_STORE_DIR   — ChromaDB persist dir (default: ./vector_store)
LINKEDIN_PDF       — Path to LinkedIn PDF (default: ./me/linkedin.pdf)
EMBED_MODEL, TOP_K, SCORE_THRESHOLD — RAG tuning
```

`BACKEND_URL` is a constant in `frontend/index.html`, not an env var.

## File Structure

```
backend/
  main.py          — FastAPI app, startup lifecycle, /chat, /visit, admin endpoints, Telegram summaries
  agent.py         — Claude agent loop, system prompt, tool dispatch
  evaluator.py     — Gemini/Groq evaluator (APPROVED/REJECTED, log-only)
  rag.py           — ChromaDB init, ingest, retrieve_context()
  memory.py        — SQLite: conversations, FAQ FTS5, leads, visits, unknown questions
  tools.py         — Tool functions + schemas, Telegram sender + queue worker
  knowledge_base/  — profile.md, projects.md, experience.md, faq.md
  me/              — linkedin.pdf (gitignored)
  vector_store/    — ChromaDB data (gitignored)
  Dockerfile       — for HuggingFace Spaces deployment (uses root requirements.txt)
frontend/
  index.html       — Portfolio + floating chat widget
```

## Non-obvious Patterns

- **Tool schemas:** `tools.py` keeps schemas with a `parameters` key; `agent.py` maps them to Anthropic's `input_schema` format.
- **Prompt caching:** the static system prompt is the first block with `cache_control`; keep anything per-request (RAG chunks, timestamps) out of it or caching breaks.
- **Chat widget renders only `**bold**` and line breaks:** the system prompt forbids headings/tables/italics; keep it that way unless `renderMarkdown()` in index.html is extended.
- **Telegram messages are HTML-escaped and truncated in `_telegram()`:** unescaped `<`, `>`, `&` or >4096 chars make Telegram reject the message.
- **Pending summaries live in memory:** a Space restart drops summaries for conversations that haven't gone idle yet.
- **Fail-open evaluator:** `evaluator.py` returns APPROVED on any exception.
- **SQLite thread safety:** `get_connection()` uses `check_same_thread=False`; don't do long write transactions.
- **Vector store init:** First run downloads ~90MB sentence-transformers model at container startup.
- **CORS:** `"null"` is included in allow_origins to support local `file://` testing of index.html.
- **faq_lookup FTS5:** simple tokenizer; `search_faq()` passes the query directly — avoid quotes in queries.

## Deployment

**Backend → HuggingFace Spaces (Docker):**
- Space: `ibryam/ibryam-chatbot`, URL `https://ibryam-ibryam-chatbot.hf.space`
- Deploy: `git push space master:main` (auth via Windows Credential Manager, user `ibryam` + HF write token)
- Secrets: ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

**Frontend → Cloudflare Pages:**
- Auto-deploys from GitHub `master` (static HTML, no build)
- Custom domain: ibryam.com

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
