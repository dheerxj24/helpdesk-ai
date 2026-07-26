"""
Classification + confidence scoring layer.

Design notes (for interview explanation):
- We do NOT trust the LLM's own self-reported confidence blindly (LLMs are
  notoriously overconfident / miscalibrated). Instead we combine THREE signals
  into one confidence score:
    1. retrieval_score   -- how similar the top KB match is (from rag.py/FAISS)
    2. score_spread       -- gap between top match and 2nd match. If the top
                              two KB articles are nearly tied, that's a sign
                              the ticket is ambiguous even if the top score
                              looks okay in isolation.
    3. classification_certainty -- the LLM's own stated certainty on category,
                              used as a MINOR signal (30% weight), not the
                              deciding factor.
- This is a deliberate design decision to defend in interviews: "why not just
  use the model's confidence field?" -> because retrieval grounding is a more
  reliable signal than a language model's self-assessment.
"""

import os
import json
from openai import OpenAI

# Groq exposes an OpenAI-compatible API -- same client library, just a
# different base_url and API key. Model is hosted on Groq's LPU hardware,
# free tier is generous and fast enough for real-time ticket classification.
GROQ_MODEL = "llama-3.1-8b-instant"

CATEGORIES = ["Network", "Access", "Hardware", "Software", "Email", "Other"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


def classify_ticket(subject: str, description: str) -> dict:
    """
    Calls GPT to classify a ticket into category + priority, with a
    self-reported certainty score (used as ONE input to the final confidence
    formula, not the whole thing -- see compute_confidence below).
    """
    prompt = f"""You are an IT ticket triage system. Classify this ticket.

Categories (pick exactly one): {", ".join(CATEGORIES)}
Priorities (pick exactly one): {", ".join(PRIORITIES)}

Priority guidance: "production down" / "cannot work at all" = Critical,
"blocked but has workaround" = High, "inconvenience" = Medium,
"cosmetic / minor" = Low.

Ticket subject: {subject}
Ticket description: {description}

Respond with ONLY valid JSON, no other text:
{{"category": "...", "priority": "...", "certainty": 0.0}}
certainty is your own confidence in this classification, 0.0 to 1.0.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=200,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if the model doesn't return clean JSON -- fail safe to
        # "Other"/"Medium" with low certainty so the ticket gets escalated
        # rather than silently mis-auto-resolved.
        parsed = {"category": "Other", "priority": "Medium", "certainty": 0.3}

    parsed.setdefault("category", "Other")
    parsed.setdefault("priority", "Medium")
    parsed.setdefault("certainty", 0.3)
    return parsed


def synthesize_resolution(description: str, kb_results: list) -> dict:
    """
    Given a ticket description and top-k retrieved KB articles, ask GPT to
    produce resolution steps GROUNDED ONLY in those articles. The model must
    explicitly say if the KB excerpts don't clearly solve the issue --
    'grounded': false is a second, independent low-confidence signal on top
    of the retrieval score.
    """
    if not kb_results:
        return {"resolution_steps": [], "grounded": False, "articles_used": []}

    kb_text = "\n\n".join(
        f"[Article {r['article'].id}] {r['article'].title}:\n{r['article'].content}"
        for r in kb_results
    )

    prompt = f"""You are resolving an IT support ticket using ONLY the knowledge
base excerpts provided below. Do not use outside knowledge. If the excerpts
don't clearly and specifically address this ticket, set "grounded" to false
rather than guessing.

Ticket: {description}

Knowledge base excerpts:
{kb_text}

Respond with ONLY valid JSON, no other text:
{{"resolution_steps": ["step 1", "step 2"], "grounded": true, "articles_used": [1, 2]}}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=400,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"resolution_steps": [], "grounded": False, "articles_used": []}

    parsed.setdefault("resolution_steps", [])
    parsed.setdefault("grounded", False)
    parsed.setdefault("articles_used", [])
    return parsed


def compute_confidence(kb_results: list, classification_certainty: float, grounded: bool) -> float:
    """
    The core confidence formula. Combines:
      - top retrieval similarity (50% weight) -- is the best KB match actually close?
      - score spread between top-2 matches (20% weight) -- is it a CLEAR winner,
        or ambiguous between two possible articles?
      - classification certainty (30% weight) -- the LLM's own stated certainty

    If the resolution synthesis step said "grounded: false", we cap confidence
    at 0.4 regardless of the other signals -- the model itself is telling us
    the KB doesn't actually answer this ticket, so we should not auto-resolve
    no matter how good the retrieval score looked.
    """
    if not kb_results:
        return 0.0

    top_score = kb_results[0]["score"]
    second_score = kb_results[1]["score"] if len(kb_results) > 1 else 0.0
    spread = max(top_score - second_score, 0.0)

    confidence = (
        0.5 * top_score
        + 0.2 * min(spread * 5, 1.0)   # scale spread so a 0.2 gap already maxes this term
        + 0.3 * classification_certainty
    )
    confidence = round(min(confidence, 1.0), 3)

    if not grounded:
        confidence = min(confidence, 0.4)

    return confidence
