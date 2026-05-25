import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


_EVAL_SYSTEM = (
    "You are a quality evaluator for an AI assistant representing Ibryam Faik on his portfolio website. "
    "Visitors are HR recruiters asking about his career.\n\n"
    "The assistant has access to a full profile document AND the specific context excerpts shown below. "
    "APPROVE if the response is professional, on-topic, and plausibly consistent with the profile of a "
    "senior data engineer (BigQuery, dbt, Tableau, Python, AI/LLM projects). "
    "REJECT only if the response is clearly fabricated, off-topic, or unprofessional.\n\n"
    'Return ONLY compact JSON: {"decision": "APPROVED" or "REJECTED", "confidence": 0-100, "reason": "one sentence"}\n'
    "No prose. No markdown. First char must be { last must be }."
)


def _build_eval_prompt(query: str, ctx: str, response: str) -> str:
    return (
        "USER QUESTION: " + query
        + "\n\nCONTEXT USED:\n" + ctx[:2000]
        + "\n\nASSISTANT RESPONSE:\n" + response
    )


def evaluate(query: str, context_chunks: list[str], response: str) -> dict:
    ctx = "\n\n".join(context_chunks) if context_chunks else "(no RAG context — general knowledge used)"
    prompt = _build_eval_prompt(query, ctx, response)

    try:
        completion = _get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _EVAL_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=150,
        )
        raw = completion.choices[0].message.content or "{}"
        # Extract JSON from the response
        start = raw.find("{")
        end = raw.rfind("}")
        blob = raw[start : end + 1] if start != -1 and end != -1 else "{}"
        data = json.loads(blob)
        decision = str(data.get("decision", "APPROVED")).upper()
        return {
            "decision": "APPROVED" if decision == "APPROVED" else "REJECTED",
            "confidence": int(data.get("confidence", 75)),
            "reason": data.get("reason", ""),
        }
    except Exception as e:
        print(f"[evaluator] error: {e} — defaulting to APPROVED")
        # Fail open: never block the user due to evaluator errors
        return {"decision": "APPROVED", "confidence": 50, "reason": f"eval_error: {e}"}
