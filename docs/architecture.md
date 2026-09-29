# Architecture

## Overview

DocuSense AI is a Retrieval-Augmented Generation (RAG) system: documents are
ingested through an OCR + extraction pipeline once, and every search or
question at query time is answered by retrieving the most relevant chunks
from a vector store and handing them to an LLM.

Two stores back the system, each serving a different kind of query:

| Store | Holds | Answers queries like |
|---|---|---|
| **SQLite** (`database.py`) | Structured fields extracted from each doc (station, severity, dates, category, contract expiry, hashes) | "list Maintenance docs for Aluva station", "contracts expiring in 30 days" |
| **ChromaDB** (`vectorstore.py`) | Chunk-level text embeddings | "signalling failures in July" (semantic, no exact keyword match needed) |

Keeping them separate is what lets the dashboard do fast structured filters
while search and the assistant do meaning-based retrieval — a single query
type (say, only a vector DB, or only SQL `LIKE`) can't do both well.

## Ingestion pipeline (upload time)

```
                POST /api/documents/upload
                          │
                          ▼
              ┌───────────────────────┐
              │ upload_validation.py  │  MIME allowlist, size limit,
              │                       │  path-traversal-safe filename
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐
              │      ocr.py           │  PyMuPDF for text-layer PDFs;
              │  PDF/Image → text     │  Tesseract OCR for scanned pages/images
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐
              │    extract.py         │  LLM call: pulls structured fields
              │  text → fields        │  (station, severity, dates, category,
              │                       │  vendor, summary, ...) as JSON
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐         ┌─────────────┐
              │    duplicate.py       │────────▶│   SQLite    │
              │  hash + fuzzy match   │         │  Document   │
              │  against existing docs│         │  row saved  │
              └───────────┬───────────┘         └─────────────┘
                          │ (skip embedding if duplicate)
                          ▼
              ┌───────────────────────┐
              │    chunking.py        │  sliding window, 800 chars,
              │  text → chunks        │  150 char overlap
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐
              │   embeddings.py       │  sentence-transformers
              │  chunks → vectors     │  (all-MiniLM-L6-v2, runs locally)
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐
              │   vectorstore.py      │  persisted ChromaDB collection,
              │  vectors → ChromaDB   │  cosine similarity index
              └───────────────────────┘
```

Each step is a plain function in its own module (`ocr.py`, `extract.py`,
`chunking.py`, `embeddings.py`, `vectorstore.py`) so the pipeline can be
tested and swapped step by step — e.g. replacing Tesseract with a
layout-aware OCR engine only touches `ocr.py`.

## Query pipeline (search / assistant time)

```
GET /api/search?q=...              POST /api/assistant/ask
        │                                    │
        ▼                                    ▼
  embed_query(q)                       embed_query(question)
        │                                    │
        ▼                                    ▼
  ChromaDB similarity search     ChromaDB similarity search (top_k chunks)
        │                                    │
        ▼                                    ▼
  ranked chunks + doc metadata     llm.py: chat(system, question + chunks)
        │                                    │
        ▼                                    ▼
  JSON results to frontend         answer + cited source chunks
```

`llm.py` wraps the OpenAI Python SDK but points `base_url` at whatever
OpenAI-compatible endpoint is configured (`LLM_BASE_URL`) — so the same code
path works against OpenAI, Groq, or a local Ollama server without changes.

## Dashboard / incident intelligence

`routers/dashboard.py` reads directly from SQLite (fast aggregate queries —
counts by category/station/severity, expiry-date filtering) and, for the
"Incident Intelligence" and "Executive Memo" features, combines those
aggregates with an LLM call to generate a narrative summary grounded in the
actual extracted fields (not free-form hallucination).

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| OCR | PyMuPDF + Tesseract | Handles both digital-text PDFs and scanned images |
| AI extraction / RAG generation | OpenAI-compatible LLM (Groq / OpenAI / Ollama) | Swappable backend, no vendor lock-in |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Runs locally, no per-call API cost, no document content leaves the network |
| Vector store | ChromaDB (persistent client) | Simple embedded vector DB, no separate server to run |
| Structured store | SQLite + SQLAlchemy | Zero-ops relational store, enough for demo/single-node scale |
| Backend | FastAPI | Async, typed, auto-generated `/docs` |
| Frontend | Vanilla JS + Chart.js | No build step, easy to audit |
| Containerization | Docker + docker-compose | One-command local deploy |

## Known scaling limits (by design, for this project's scope)

- SQLite and the ChromaDB persistent client are single-writer; this is fine
  for a demo / single-instance deployment but would need Postgres + a
  standalone vector DB (or pgvector) for multi-instance production use.
- The chunker is a fixed character-window splitter, not token-aware or
  layout-aware — adequate for prose-heavy reports, less precise for tables.
