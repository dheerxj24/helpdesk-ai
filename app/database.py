"""
DB connection setup. Reads DATABASE_URL from the environment so the same
code works against local SQLite (dev) and Render Postgres (production) --
no code change needed to switch, just the env var.

Render's Postgres "Internal Database URL" starts with `postgres://`, but
SQLAlchemy 1.4+/2.x requires the `postgresql://` scheme -- we normalize
that below so copy-pasting Render's URL directly just works.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./helpdesk.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# check_same_thread is a SQLite-only quirk; Postgres doesn't need/accept it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session per-request, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()