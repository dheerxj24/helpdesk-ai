"""
DB connection setup. Using SQLite for local dev -- swapping to Postgres later
only requires changing DATABASE_URL (SQLAlchemy handles the rest).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

DATABASE_URL = "sqlite:///./helpdesk.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # needed only for SQLite
)
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
