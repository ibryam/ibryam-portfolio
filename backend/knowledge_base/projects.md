# Ibryam Faik — Projects

## 1. Swiss Macro Monitor
**Type:** End-to-end data pipeline + live Tableau dashboard
**Tech:** dbt Core, Google BigQuery, Python, GitHub Actions, Tableau Public
**Live dashboard:** https://public.tableau.com/app/profile/ibryam/viz/SwissMacroMonitor/Overview
**GitHub:** https://github.com/ibryam/swiss-macro-monitor

A real-time Swiss economic tracking system that monitors 15 economic indicators including interest rates, GDP, inflation, unemployment, and exchange rates.

Key features:
- Tracks 15 Swiss economic indicators across 3 data sources
- 27 automated data quality tests to ensure reliability
- Monthly automated refresh via GitHub Actions
- Zero infrastructure cost using free-tier cloud services
- Full dbt project with staging, intermediate, and mart layers
- Management-ready Tableau dashboard with trend analysis

This project demonstrates the complete modern data stack: ingestion → transformation (dbt) → warehouse (BigQuery) → visualization (Tableau).

---

## 2. SMI Risk Monitor
**Type:** Daily automated pipeline + live risk dashboard
**Tech:** Python, Google BigQuery, GitHub Actions, Tableau Public
**Live dashboard:** https://public.tableau.com/app/profile/ibryam/viz/SMIRiskMonitor/Performance
**GitHub:** https://github.com/ibryam/smi-risk-monitor

A daily risk monitoring system for the Swiss Market Index (SMI) tracking performance and volatility metrics for 20 stocks.

Key features:
- Monitors 20 SMI stocks with daily automated pipeline
- Performance and volatility metrics across 3 dashboard tabs
- Daily automated data refresh via GitHub Actions
- Risk scoring and trend detection

---

## 3. ATS Skipper v2
**Type:** AI-powered job application automation tool
**Tech:** Python, Gemini 2.5 Flash, Groq (llama-3.3-70b), LinkedIn scraping, Selenium, docx generation
**GitHub:** https://github.com/ibryam/ats-skipper

An automated job application workflow that scrapes multiple job boards, scores each listing against your profile using 8 evaluation dimensions, and generates tailored CVs and cover letters.

Key features:
- Scrapes 4 job boards: LinkedIn, jobs.ch, jobscout24.ch, xing.com
- Multi-dimensional ATS scoring (8 dimensions: skills 35%, tech 25%, seniority 20%, language 10%, industry 5%, location 5%)
- Letter grade output (A+/A/B+/B/C+/C/D/F) for each job
- AI-generated tailored CV as .docx per application
- Cover letter generation (German JD → German cover letter)
- Application tracking CSV with 20-column schema
- Pushover/Telegram notifications on high-scoring matches
- Gemini 2.5 Flash as primary LLM, Groq as fallback

This is one of the most complex personal projects — multi-agent architecture with scraping, scoring, generation, and tracking all automated.

---

## 4. Flight Deals Finder
**Type:** Weekly automated flight price monitor + Telegram alerts
**Tech:** Python, SerpAPI, Google Sheets (Sheety), GitHub Actions, Telegram Bot API
**GitHub:** https://github.com/ibryam/flight-deals

A weekly automated tool that monitors flight prices from configured origins to destinations and sends Telegram alerts when prices drop below user-defined thresholds.

Key features:
- Runs every Monday 6am UTC via GitHub Actions (fully automated, no server needed)
- Configurable origins and destinations via Google Sheet
- Price threshold per destination (separate one-way / return thresholds)
- Telegram notification with airline, price, Google Flights link
- Example: SOF → MAD return under €200 → instant alert

---

## 5. AI Career Chatbot (ibryam.com)
**Type:** Agentic AI chatbot embedded in personal portfolio
**Tech:** Python, FastAPI, Gemini 2.5 Flash, Groq (llama-3.3-70b), ChromaDB, LangChain, SQLite, Pushover, HuggingFace Spaces, Cloudflare Pages

A personal AI assistant that represents Ibryam on his portfolio website. HR recruiters can ask questions about his experience, projects, skills, and background, and get accurate, grounded answers.

Key features:
- RAG (Retrieval-Augmented Generation) over personal documents — answers are grounded in actual profile data
- FAQ SQLite database with full-text search — structured answers to common HR questions
- Conversation memory — remembers context within a session
- Groq evaluator (llama-3.3-70b) as second LLM quality gate — APPROVED/REJECTED decision per response
- Agentic Pushover notifications — alerts Ibryam when a question can't be answered or a recruiter shares their email
- Agent tools: record_user_details, record_unknown_question, faq_lookup, get_session_context
- Custom floating chat widget matching the portfolio's navy/teal design
- Deployed free: HuggingFace Spaces (backend) + Cloudflare Pages (frontend)

---

## 6. Local AI Agent v2
**Type:** Local AI assistant with tool use and persistent memory
**Tech:** Python, Streamlit, Ollama (qwen3:8b), LangChain, LangGraph, SQLite checkpointing, Tavily Search

A locally-running AI assistant powered by open-source models. No API costs — runs entirely on local hardware.

Key features:
- 6 agent tools: web search, get_date, read_file, write_file, list_directory, run_command (PowerShell)
- Persistent conversation memory across sessions via LangGraph SQLite
- Multi-model support (qwen3:8b, qwen2.5, llama3.2, qwen3.6) switchable from UI
- Token usage tracking in sidebar
- URL-based session persistence

---

## 7. My Local AI Agent v1
**Type:** First version of local AI assistant
**Tech:** Python, Gradio, Ollama (qwen3:8b), LangChain, Tavily Search, SQLite

Simpler predecessor to v2. Gradio UI, web search + date tool, persistent memory. Built as a learning project before v2.
