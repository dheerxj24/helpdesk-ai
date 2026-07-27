"""
Entry point. For now (Day 1-2 scope): app setup, DB init, and basic
create/list/get endpoints for tickets and KB articles -- no AI pipeline yet,
that comes in step 3-4 (rag.py, classify.py).

Run with: uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs for interactive API docs.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.database import init_db, get_db, SessionLocal
from app import models, rag, classify

THRESHOLD_AUTO = 0.80      # >= this -> auto-resolve
THRESHOLD_SUGGEST = 0.55   # >= this (but < AUTO) -> suggest to agent, else escalate

app = FastAPI(title="IT Helpdesk Auto-Resolver")

# Allow the local Vite dev server, the production Vercel domain, and any
# Vercel preview deployment for this project (Vercel generates a new,
# unpredictable subdomain per branch/commit -- e.g.
# helpdesk-ai-git-main-dheerajpaul24-4921s-projects.vercel.app -- so a fixed
# allow_origins list can't cover those; the regex below matches any
# *.vercel.app subdomain belonging to this project).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://helpdesk-ai-ten.vercel.app",
    ],
    allow_origin_regex=r"https://helpdesk-ai.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------- Pydantic schemas (request/response shapes) ----------

class TicketCreate(BaseModel):
    subject: str
    description: str


class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str
    confidence_score: Optional[float] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class KBArticleCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[list[str]] = []


class KBArticleOut(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str] = None
    tags: list[str] = []

    class Config:
        from_attributes = True


# ---------- Ticket endpoints ----------

@app.post("/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """
    Full pipeline:
      1. Save the raw ticket (status=open)
      2. Classify (category, priority, LLM's own certainty)
      3. RAG retrieval -- top-k KB articles for this ticket's description
      4. Resolution synthesis -- grounded steps from the retrieved articles
      5. Confidence scoring -- combines retrieval + classification + groundedness
      6. Route: auto_resolve / suggest / escalate based on threshold
      7. Log everything to resolution_logs for auditability + analytics
    """
    ticket = models.Ticket(
        subject=payload.subject,
        description=payload.description,
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    full_text = f"{payload.subject}. {payload.description}"

    # Step 2: classify
    classification = classify.classify_ticket(payload.subject, payload.description)

    # Step 3: retrieve
    kb_results = rag.search(db, full_text, top_k=3)

    # Step 4: synthesize resolution grounded in retrieved articles
    synthesis = classify.synthesize_resolution(payload.description, kb_results)

    # Step 5: confidence
    confidence = classify.compute_confidence(
        kb_results,
        classification["certainty"],
        synthesis["grounded"],
    )

    # Step 6: route
    if confidence >= THRESHOLD_AUTO:
        decision = "auto_resolve"
        ticket.status = "auto_resolved"
        ticket.resolution = "\n".join(synthesis["resolution_steps"]) or None
        ticket.resolved_by = "ai"
        ticket.resolved_at = datetime.utcnow()
    elif confidence >= THRESHOLD_SUGGEST:
        decision = "suggest"
        ticket.status = "open"   # stays open, but agent sees a suggested resolution
        ticket.resolution = "\n".join(synthesis["resolution_steps"]) or None
    else:
        decision = "escalate"
        ticket.status = "escalated"

    ticket.category = classification["category"]
    ticket.priority = classification["priority"]
    ticket.confidence_score = confidence

    db.commit()
    db.refresh(ticket)

    # Step 7: log the decision for analytics/audit
    log = models.ResolutionLog(
        ticket_id=ticket.id,
        predicted_category=classification["category"],
        confidence_score=confidence,
        kb_articles_matched=[r["article"].id for r in kb_results],
        decision=decision,
        threshold_used=THRESHOLD_AUTO,
    )
    db.add(log)
    db.commit()

    return ticket


@app.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Ticket)
    if status:
        query = query.filter(models.Ticket.status == status)
    if category:
        query = query.filter(models.Ticket.category == category)
    return query.order_by(models.Ticket.created_at.desc()).all()


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# ---------- KB article endpoints ----------

@app.post("/kb/articles", response_model=KBArticleOut)
def create_kb_article(payload: KBArticleCreate, db: Session = Depends(get_db)):
    """
    Adds a KB article. Embedding generation + FAISS indexing will be wired
    in when rag.py is added (step 3) -- this just persists the raw article
    for now so we have seed data ready.
    """
    article = models.KBArticle(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=payload.tags,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    rag.build_index(db)  # keep the FAISS index in sync with the DB
    return article


@app.get("/kb/articles", response_model=list[KBArticleOut])
def list_kb_articles(db: Session = Depends(get_db)):
    return db.query(models.KBArticle).all()


@app.get("/kb/search")
def search_kb(q: str, top_k: int = 3, db: Session = Depends(get_db)):
    """
    Debug endpoint: raw RAG retrieval for a query string. Lets you sanity-check
    that embeddings + FAISS are actually matching sensible KB articles before
    wiring this into the full ticket pipeline (classify.py, step 4).
    """
    results = rag.search(db, q, top_k=top_k)
    return [
        {
            "article_id": r["article"].id,
            "title": r["article"].title,
            "category": r["article"].category,
            "score": round(r["score"], 4),
        }
        for r in results
    ]


@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    """
    High-level numbers for the dashboard: total ticket volume, breakdown by
    status (auto-resolved vs escalated vs open), auto-resolve rate, and
    average confidence. This is what a hiring manager would expect an
    "analytics" feature to show without over-building it.
    """
    total = db.query(models.Ticket).count()
    if total == 0:
        return {"total_tickets": 0}

    auto_resolved = db.query(models.Ticket).filter(models.Ticket.status == "auto_resolved").count()
    escalated = db.query(models.Ticket).filter(models.Ticket.status == "escalated").count()
    open_suggested = db.query(models.Ticket).filter(models.Ticket.status == "open").count()

    avg_confidence = db.query(models.Ticket).filter(
        models.Ticket.confidence_score.isnot(None)
    ).all()
    avg_conf_value = (
        round(sum(t.confidence_score for t in avg_confidence) / len(avg_confidence), 3)
        if avg_confidence else None
    )

    # category breakdown
    categories = {}
    for t in db.query(models.Ticket).filter(models.Ticket.category.isnot(None)).all():
        categories[t.category] = categories.get(t.category, 0) + 1

    return {
        "total_tickets": total,
        "auto_resolved": auto_resolved,
        "escalated": escalated,
        "open_or_suggested": open_suggested,
        "auto_resolve_rate": round(auto_resolved / total, 3),
        "average_confidence": avg_conf_value,
        "tickets_by_category": categories,
    }


@app.get("/analytics/confidence-dist")
def confidence_distribution(db: Session = Depends(get_db)):
    """
    Histogram-style breakdown of confidence scores into 5 buckets (0-0.2,
    0.2-0.4, ..., 0.8-1.0). Useful for visually deciding whether the current
    thresholds (0.55 / 0.80) actually sit at sensible cut points given the
    real distribution of scores, rather than picking them arbitrarily.
    """
    logs = db.query(models.ResolutionLog).all()
    buckets = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for log in logs:
        score = log.confidence_score or 0.0
        if score < 0.2:
            buckets["0.0-0.2"] += 1
        elif score < 0.4:
            buckets["0.2-0.4"] += 1
        elif score < 0.6:
            buckets["0.4-0.6"] += 1
        elif score < 0.8:
            buckets["0.6-0.8"] += 1
        else:
            buckets["0.8-1.0"] += 1
    return {"total_logged_decisions": len(logs), "buckets": buckets}


class ThresholdUpdate(BaseModel):
    threshold_auto: Optional[float] = None
    threshold_suggest: Optional[float] = None


@app.get("/admin/threshold")
def get_threshold():
    """Returns the current in-memory threshold values."""
    return {"threshold_auto": THRESHOLD_AUTO, "threshold_suggest": THRESHOLD_SUGGEST}


@app.post("/admin/threshold")
def update_threshold(payload: ThresholdUpdate):
    """
    Lets you tune the auto-resolve / suggest thresholds at runtime instead of
    hardcoding them -- demonstrates that the confidence cutoffs are a tunable
    parameter, not a magic number baked into the code. Note: this changes the
    values in-memory for the running process; a persistent version would
    store these in the DB or a config table instead.
    """
    global THRESHOLD_AUTO, THRESHOLD_SUGGEST
    if payload.threshold_auto is not None:
        THRESHOLD_AUTO = payload.threshold_auto
    if payload.threshold_suggest is not None:
        THRESHOLD_SUGGEST = payload.threshold_suggest
    return {"threshold_auto": THRESHOLD_AUTO, "threshold_suggest": THRESHOLD_SUGGEST}


@app.get("/")
def root():
    return {"status": "ok", "message": "IT Helpdesk Auto-Resolver API running"}