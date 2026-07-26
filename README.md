# IT Helpdesk Auto-Resolver

## What's built so far (steps 1-6 complete)
- FastAPI app with ticket + KB article CRUD
- SQLite DB via SQLAlchemy (schema: tickets, kb_articles, resolution_logs, agents)
- RAG retrieval: sentence-transformers embeddings + FAISS similarity search
- Classification + confidence scoring via Groq (Llama 3.1, OpenAI-compatible API)
- Confidence-based routing: auto_resolve / suggest / escalate
- Analytics endpoints: summary stats + confidence distribution
- Runtime-tunable thresholds

## Not built yet
- Frontend dashboard (React)
- Deployment

## How to run

```bash
pip install -r requirements.txt
python seed_kb.py            # creates helpdesk.db + seeds KB articles
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive Swagger UI.

To populate demo tickets with realistic variety (run in a separate terminal
while the server is running):
```bash
python seed_tickets.py
```

Requires a `.env` file with:
```
GROQ_API_KEY=your_key_here
```
Get a free key at console.groq.com.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /tickets` | Create a ticket -- runs full pipeline (classify, retrieve, score, route) |
| `GET /tickets` | List tickets, filter by status/category |
| `GET /tickets/{id}` | Get one ticket |
| `POST /kb/articles` | Add a KB article (rebuilds FAISS index) |
| `GET /kb/articles` | List KB articles |
| `GET /kb/search?q=` | Debug: raw RAG retrieval for a query |
| `GET /analytics/summary` | Volume, auto-resolve rate, category breakdown |
| `GET /analytics/confidence-dist` | Histogram of confidence scores |
| `POST /admin/threshold` | Update auto-resolve/suggest thresholds at runtime |

## Folder structure
```
app/
  main.py       -> FastAPI app + endpoints
  models.py     -> DB schema (SQLAlchemy models)
  database.py   -> DB session/connection setup
  rag.py        -> embeddings + FAISS retrieval
  classify.py   -> LLM classification + confidence scoring
seed_kb.py      -> populates demo KB articles
seed_tickets.py -> populates demo tickets through the full pipeline
requirements.txt
```

## Design decisions worth explaining in an interview
- **Confidence formula is NOT just the LLM's self-reported score.** It combines
  retrieval similarity (50%), score spread between top-2 KB matches (20%), and
  classification certainty (30%) -- plus a hard cap at 0.4 if the resolution
  synthesis step says the KB doesn't actually ground the ticket. Retrieval
  grounding is more reliable than a language model's self-assessment.
- **Three-tier routing** (auto_resolve / suggest / escalate), not a binary
  yes/no -- mirrors how real helpdesk systems avoid over-trusting automation.
- **SQLite now, Postgres-ready later** -- only DATABASE_URL changes.
- **Local embeddings (sentence-transformers) instead of a paid embeddings API**
  -- cost-conscious, and FAISS flat index is right-sized for KB article counts
  in the dozens/hundreds (no need for IVF/HNSW at this scale).
- **resolution_logs table exists from day 1** -- audit trail is a design
  decision, not bolted on after the fact.