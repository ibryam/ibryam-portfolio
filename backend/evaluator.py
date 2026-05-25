import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

# Gemini via OpenAI-compatible endpoint (primary — 15 RPM free on gemini-2.0-flash)
_gemini_client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
GEMINI_EVAL_MODEL = os.getenv("GEMINI_EVAL_MODEL", "gemini-2.0-flash")

# Groq via OpenAI-compatible endpoint (fallback if Gemini fails/rate-limits)
_groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
GROQ_EVAL_MODEL = os.getenv("GROQ_EVAL_MODEL", "llama-3.1-8b-instant")

_EVAL_SYSTEM = (
    "You are a quality evaluator for an AI assistant representing Ibryam Faik on his portfolio website. "
    "Visitors are HR recruiters asking about his career as a senior data engineer.\n\n"
    "APPROVE if the response is professional, on-topic, and plausibly consistent with a senior data "
    "engineer's profile (BigQuery, dbt, Tableau, Python, AI/LLM projects, DACH career goals).\n"
    "REJECT only if the response is clearly fabricated, off-topic, or unprofessional.\n\n"
    'Return ONLY compact JSON: {"decision": "APPROVED" or "REJECTED", "confidence": 0-100, "reason": "one sentence"}\n'
    "No prose. No markdown. First char must be { last must be }."
)


def _build_eval_prompt(query: str, ctx: str, response: str) -> str:
    return (
        "USER QUESTION: " + query
        + "\n\nCONTEXT:\n" + ctx[:1500]
        + "\n\nASSISTANT RESPONSE:\n" + response
    )


def _parse_verdict(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    blob = raw[start: end + 1] if start != -1 and end != -1 else "{}"
    data = json.loads(blob)
    decision = str(data.get("decision", "APPROVED")).upper()
    return {
        "decision": "APPROVED" if decision == "APPROVED" else "REJECTED",
        "confidence": int(data.get("confidence", 75)),
        "reason": data.get("reason", ""),
    }


def _call_eval(client: OpenAI, model: str, prompt: str) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _EVAL_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=150,
    )
    raw = completion.choices[0].message.content or "{}"
    return _parse_verdict(raw)


def evaluate(query: str, context_chunks: list[str], response: str) -> dict:
    ctx = "\n\n".join(context_chunks) if context_chunks else "(no RAG context)"
    prompt = _build_eval_prompt(query, ctx, response)

    # Try Gemini first
    try:
        return _call_eval(_gemini_client, GEMINI_EVAL_MODEL, prompt)
    except Exception as e:
        print(f"[evaluator] Gemini failed ({e}) — falling back to Groq")

    # Fall back to Groq
    try:
        return _call_eval(_groq_client, GROQ_EVAL_MODEL, prompt)
    except Exception as e:
        print(f"[evaluator] Groq also failed ({e}) — defaulting to APPROVED")

    return {"decision": "APPROVED", "confidence": 50, "reason": "eval_unavailable"}
