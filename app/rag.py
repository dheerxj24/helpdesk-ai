"""
RAG retrieval layer.

Design notes (for interview explanation):
- We use sentence-transformers (all-MiniLM-L6-v2) for embeddings -- it's small
  (~80MB), runs locally/free, and is good enough for short IT-ticket-style text.
  No need for a heavier/paid embedding API at this scale.
- FAISS (IndexFlatL2) is used for similarity search. For our KB size (dozens to
  low-hundreds of articles) an exact flat index is fine -- no need for
  approximate-nearest-neighbor indexes (IVF, HNSW) which only pay off at
  much larger scale. This is a good "right-sized, not over-engineered" point
  to make in an interview.
- The FAISS index lives in memory and is rebuilt from the DB on startup. For a
  demo/project this is fine. In a "real" production system you'd persist the
  index to disk and update it incrementally instead of rebuilding from scratch
  every time -- worth mentioning if asked "how would you scale this".
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app import models

_model = None
_index = None
_article_ids = []  # maps FAISS row position -> KBArticle.id


def get_model():
    """Lazy-load the embedding model (loading it is slow, do it once)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> np.ndarray:
    model = get_model()
    vec = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
    return vec.astype("float32")


def build_index(db: Session):
    """
    Rebuilds the FAISS index from all KB articles currently in the DB.
    Call this on app startup, and again any time a KB article is added
    (see main.py -- create_kb_article calls this after inserting).
    """
    global _index, _article_ids

    articles = db.query(models.KBArticle).all()
    if not articles:
        _index = None
        _article_ids = []
        return

    model = get_model()
    # embed title + content together -- title carries a lot of signal for
    # short IT tickets ("VPN Not Connecting" alone is often enough to match)
    texts = [f"{a.title}. {a.content}" for a in articles]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    embeddings = embeddings.astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine similarity
    index.add(embeddings)

    _index = index
    _article_ids = [a.id for a in articles]


def search(db: Session, query: str, top_k: int = 3):
    """
    Returns top_k matching KB articles for a query string, each with a
    similarity score in [-1, 1] (cosine similarity since vectors are
    normalized). Higher = more similar.

    Returns: list of dicts: {"article": KBArticle, "score": float}
    """
    if _index is None or _index.ntotal == 0:
        return []

    query_vec = embed_text(query)
    scores, indices = _index.search(query_vec, min(top_k, _index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        article_id = _article_ids[idx]
        article = db.query(models.KBArticle).filter(models.KBArticle.id == article_id).first()
        if article:
            results.append({"article": article, "score": float(score)})
    return results
