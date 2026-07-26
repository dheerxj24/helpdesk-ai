"""
RAG retrieval layer.

Design notes (for interview explanation):
- Embeddings come from Cohere's hosted Embed API (embed-english-v3.0) instead
  of a locally-loaded sentence-transformers model. This was a deliberate
  change from the original design: local embeddings meant importing
  torch + sentence-transformers, which alone is enough RAM to OOM a 512MB
  Render free-tier instance during startup/import -- before the app could
  even bind its port. Calling a hosted embeddings API removes that entire
  dependency chain, at the cost of a network round-trip per embed call and
  a dependency on Cohere's free tier being available.
- FAISS (IndexFlatIP) is still used for the actual similarity search --
  it's a lightweight, torch-free C++ library, so keeping it in-process is
  fine. Only the embedding STEP moved to a hosted API, not the index/search.
- Cohere's v3 embed models require an `input_type` ("search_document" for
  things being indexed, "search_query" for the incoming search text) --
  this asymmetric embedding is actually a quality improvement over the old
  symmetric sentence-transformers setup, worth mentioning if asked.
- The FAISS index lives in memory and is rebuilt from the DB on app startup
  (see main.py on_startup) and whenever a KB article is added.
"""

import os
import numpy as np
import requests
from sqlalchemy.orm import Session

from app import models

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
COHERE_EMBED_URL = "https://api.cohere.com/v1/embed"
COHERE_MODEL = "embed-english-v3.0"

_index = None
_article_ids = []  # maps FAISS row position -> KBArticle.id


def _get_embeddings(texts: list[str], input_type: str) -> np.ndarray:
    """
    Calls Cohere's Embed API for a batch of texts and returns L2-normalized
    float32 vectors (normalized so FAISS IndexFlatIP == cosine similarity,
    matching the old sentence-transformers normalize_embeddings=True setup).
    """
    if not COHERE_API_KEY:
        raise RuntimeError(
            "COHERE_API_KEY is not set. Get a free key at "
            "dashboard.cohere.com/api-keys and set it as an env var."
        )

    response = requests.post(
        COHERE_EMBED_URL,
        headers={
            "Authorization": f"Bearer {COHERE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": COHERE_MODEL,
            "texts": texts,
            "input_type": input_type,
            "embedding_types": ["float"],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # v1 embed responses: either {"embeddings": [[...], ...]} or, with
    # embedding_types set, {"embeddings": {"float": [[...], ...]}}
    embeddings = data["embeddings"]
    if isinstance(embeddings, dict):
        embeddings = embeddings["float"]

    vecs = np.array(embeddings, dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # avoid divide-by-zero on a degenerate embedding
    return vecs / norms


def embed_text(text: str) -> np.ndarray:
    """Embed a single QUERY string (used at search time)."""
    return _get_embeddings([text], input_type="search_query")


def build_index(db: Session):
    """
    Rebuilds the FAISS index from all KB articles currently in the DB.
    Call this on app startup, and again any time a KB article is added
    (see main.py -- create_kb_article calls this after inserting).
    """
    import faiss

    global _index, _article_ids

    articles = db.query(models.KBArticle).all()
    if not articles:
        _index = None
        _article_ids = []
        return

    # embed title + content together -- title carries a lot of signal for
    # short IT tickets ("VPN Not Connecting" alone is often enough to match)
    texts = [f"{a.title}. {a.content}" for a in articles]
    embeddings = _get_embeddings(texts, input_type="search_document")

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