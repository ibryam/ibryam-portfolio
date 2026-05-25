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


EVAL_PROMPT = """You are a strict evaluator reviewing an AI assistant's response on behalf of a job candidate's portfolio.

The assistant is acting as Ibryam Faik and answering questions from HR recruiters.

Your task: decide if the response is APPROVED or REJECTED.

APPROVE if:
- The response accurately answers the question using the provided context
- The tone is professional and represents the candidate well
- No false claims or invented facts

REJECT if:
- The response contains fabricated facts not in the context
- The response is off-topic or irrelevant
- The response is unprofessional or harmful

Return ONLY a compact JSON object with these exact keys:
{"decision": "APPROVED" or "REJECTED", "confidence": 0-100, "reason": "one sentence"}

No prose. No markdown. First char must be {{ last must be }}.

---
USER QUESTION: {query}

CONTEXT USED:
{context}

ASSISTANT RESPONSE:
{response}
"""


def evaluate(query: str, context_chunks: list[str], response: str) -> dict:
    ctx = "\n\n".join(context_chunks) if context_chunks else "(no RAG context — general knowledge used)"
    prompt = EVAL_PROMPT.format(query=query, context=ctx[:2000], response=response)

    try:
        completion = _get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Return strict JSON only. No prose."},
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
