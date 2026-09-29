# Setup Guide

Two ways to run DocuSense AI: Docker (recommended — one command, OCR
dependencies included) or a local Python environment.

## Option 1 — Docker

**Requirements:** Docker + Docker Compose.

```bash
git clone https://github.com/25-THEBEaST-25/KMRL-DocuSense.git
cd KMRL-DocuSense
cp .env.example .env
```

Edit `.env` and set an LLM key — pick one of the three options already
commented in the file (Groq is free and fastest to get running):

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=<your groq key>
LLM_MODEL=llama-3.1-70b-versatile
```

Then:

```bash
docker-compose up --build
```

This builds the backend image (Python 3.11 + Tesseract + Poppler baked in)
and serves the static frontend via nginx.

- Backend: http://localhost:8000 (interactive API docs at `/docs`)
- Frontend: http://localhost:3000

Uploaded files, the SQLite DB, and the ChromaDB vector store persist in
`./data/` on the host (mounted as a volume), so they survive
`docker-compose down` / `up` cycles.

To load the 95 sample KMRL documents into the running backend container:

```bash
docker-compose exec backend python seed_db.py
```

## Option 2 — Local Python environment

**System dependencies** (OCR needs these installed natively):

```bash
# macOS
brew install tesseract poppler

# Ubuntu / Debian
sudo apt install tesseract-ocr poppler-utils

# Windows
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki (add to PATH)
# Poppler:   https://github.com/oschwartz10612/poppler-windows/releases (add bin/ to PATH)
```

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # set LLM_API_KEY etc. — see file for provider options
python seed_db.py               # loads 95 sample KMRL documents
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs, or
`http://localhost:8000/health` for a liveness check.

**Frontend** (no build step):

```bash
cd frontend
python -m http.server 5500
```

Visit `http://localhost:5500`.

## Verifying it worked

1. Open the frontend and go to the **Documents** tab — you should see the
   95 seeded documents (if you ran `seed_db.py`).
2. Go to **Search** and try `signalling failures in July` — you should get
   ranked semantic results, not just keyword matches.
3. Go to **AI Assistant** and ask a question — if you see an error here but
   search works fine, double-check `LLM_API_KEY` / `LLM_BASE_URL` in `.env`
   (search and the dashboard work without an LLM key; the assistant and
   field extraction on new uploads do not).
4. Upload a new PDF or image on the **Upload** tab and confirm it gets
   OCR'd, classified, and shows up in Documents.

## API endpoint reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Run a file through the full ingestion pipeline |
| `GET` | `/api/documents` | List all indexed documents (filter by `category`, `station`) |
| `GET` | `/api/documents/{id}` | Get one document's full record |
| `GET` | `/api/search?q=...&top_k=6` | Semantic search over chunk embeddings |
| `POST` | `/api/assistant/ask` | RAG Q&A grounded in indexed documents, with cited sources |
| `GET` | `/api/dashboard/stats` | KPI counts, category/station breakdowns |
| `GET` | `/api/dashboard/incident-intelligence` | LLM-generated fault trend analysis |
| `GET` | `/api/dashboard/expiring-contracts` | Contracts/SOPs expiring in the next 30 days |
| `GET` | `/health` | Liveness check (used by the Docker healthcheck) |

See [architecture.md](architecture.md) for how these endpoints fit into the
RAG pipeline.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `docker-compose up` backend container stuck "unhealthy" | Check `docker-compose logs backend` — usually a missing/invalid `LLM_API_KEY` isn't the cause (search/dashboard don't need it), so look for a startup exception instead |
| Upload fails with "No readable text found" | Scanned image is too low quality for Tesseract, or the file has no text layer at all |
| AI Assistant returns generic/empty answers | No documents indexed yet (run `seed_db.py`) or `LLM_API_KEY` not set |
| `ModuleNotFoundError` running locally | Activate the venv and re-run `pip install -r requirements.txt` from inside `backend/` |
