"""
Database models for the IT Helpdesk Auto-Resolver.

Design notes (for interview explanation):
- tickets: the core entity, tracks lifecycle (open -> auto_resolved/escalated -> closed)
- kb_articles: knowledge base used for RAG retrieval
- resolution_logs: audit trail of every AI decision (category, confidence, which
  KB articles were matched, and whether it auto-resolved or escalated). This
  table is what powers the analytics dashboard and lets us explain/debug any
  decision after the fact -- important for trust in an automated system.
- agents: human agents who receive escalated tickets
"""

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50))          # Network, Access, Hardware, Software, Email, Other
    priority = Column(String(20))          # Low, Medium, High, Critical
    status = Column(String(20), default="open")  # open, auto_resolved, escalated, closed
    confidence_score = Column(Float)
    resolution = Column(Text)
    resolved_by = Column(String(20))       # "ai" or "human"
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    logs = relationship("ResolutionLog", back_populates="ticket")


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50))
    tags = Column(JSON, default=list)       # stored as JSON list, no need for pg array type
    created_at = Column(DateTime, default=datetime.utcnow)
    # NOTE: embeddings are NOT stored in the relational DB -- they live in the
    # FAISS index (see rag.py). We only keep a parallel id->article mapping so
    # FAISS result indices can be resolved back to real KB rows.


class ResolutionLog(Base):
    __tablename__ = "resolution_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    predicted_category = Column(String(50))
    confidence_score = Column(Float)
    kb_articles_matched = Column(JSON, default=list)  # list of article IDs
    decision = Column(String(20))           # auto_resolve, suggest, escalate
    threshold_used = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="logs")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    specialty = Column(String(50))
    active_tickets = Column(Integer, default=0)
