# Kochi Metro — AI Document Intelligence System

A working RAG-based document intelligence platform for Kochi Metro Rail Limited (KMRL).
Replaces manual PDF search with AI understanding, natural language search, and an
internal AI assistant.

## Architecture

```
PDF/Image Upload
      │
      ▼
   OCR (pytesseract / PyMuPDF)          [ocr.py]
      │
      ▼
AI Field Extraction + Classification    [extract.py]  → structured fields in SQLite
      │
      ▼
   Chunking                             [chunking.py]
      │
      ▼
   Embedding (sentence-transformers)    [embeddings.py]
      │
      ▼
   Vector DB (ChromaDB)                 [vectorstore.py]
      │
      ▼
   LLM (RAG query time)                 [llm.py + routers/assistant.py]
      │
      ▼
   Answer + Sources
```

Structured metadata (dates, stations, severity, etc.) → **SQLite**
Chunk embeddings for semantic search → **ChromaDB**
This split is what makes both the "search by field" (dashboard filters) AND
"search by meaning" (natural language) features work well.

## File structure

```
kochi-metro-ai/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── database.py               # SQLite models (Document table)
│   ├── ocr.py                    # Step 1: PDF/Image -> text
│   ├── extract.py                # AI structured field extraction + classification
│   ├── chunking.py               # Step 2: text -> chunks
│   ├── embeddings.py             # Step 3: chunks -> vectors (local model)
│   ├── vectorstore.py            # Step 4: ChromaDB wrapper
│   ├── llm.py                    # OpenAI-compatible LLM wrapper (RAG generation)
│   ├── duplicate.py              # Duplicate detection (hash + fuzzy match)
│   ├── requirements.txt
│   ├── .env.example              # copy to .env and fill in
│   └── routers/
│       ├── upload.py             # POST /api/documents/upload  (full pipeline)
│       ├── search.py             # GET  /api/search            (semantic search)
│       ├── assistant.py          # POST /api/assistant/ask     (RAG Q&A)
│       └── dashboard.py          # GET  /api/dashboard/*       (stats, insights, expiry alerts)
├── frontend/
│   ├── index.html                # Single-page app (4 tabs)
│   ├── style.css
│   └── app.js                    # calls the API, renders charts (Chart.js)
├── data/
│   ├── uploads/                  # raw uploaded files land here
│   └── chroma_db/                # vector DB storage (auto-created)
└── README.md
```

## Step-by-step setup

### 1. System dependencies (needed for OCR)

**Windows:**
- Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki (add to PATH)
- Install Poppler: https://github.com/oschwartz10612/poppler-windows/releases (add `bin/` to PATH)

**Mac:**
```bash
brew install tesseract poppler
```

**Linux:**
```bash
sudo apt install tesseract-ocr poppler-utils
```

### 2. Backend setup

```bash
cd kochi-metro-ai/backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure LLM key

```bash
cp .env.example .env
```
Open `.env` and pick ONE option:
- **Groq (recommended — free & fast for hackathon):** get a key at https://console.groq.com, paste into `LLM_API_KEY`
- **OpenAI:** uncomment Option A, add your key
- **Fully offline (Ollama):** install Ollama, `ollama pull llama3.1`, uncomment Option C

### 4. Run the backend

```bash
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to see/test all API endpoints interactively.

### 5. Run the frontend

No build step needed — just open the file, or serve it:
```bash
cd ../frontend
python -m http.server 5500
```
Visit `http://localhost:5500`

### 6. Try it end to end

1. Go to **Upload** tab, upload a sample maintenance report PDF (even a scanned one).
2. Watch it get OCR'd, classified, and structured fields extracted.
3. Go to **Search** tab → try "signalling failures in July"
4. Go to **AI Assistant** tab → ask "What is the SOP for emergency evacuation?" (works best once you've uploaded an SOP doc)
5. Go to **Dashboard** tab → see stats, charts, AI insights, expiring contracts

## Feature → code map

| Feature in your spec | File |
|---|---|
| 1. AI Document Understanding | `extract.py` |
| 2. Natural Language Search | `vectorstore.py` + `routers/search.py` |
| 3. AI Assistant | `routers/assistant.py` |
| 4. RAG pipeline | `ocr.py` → `chunking.py` → `embeddings.py` → `vectorstore.py` → `llm.py` |
| 5. OCR | `ocr.py` |
| 6. Smart Classification | `extract.py` (category field) |
| 7. Duplicate Detection | `duplicate.py` |
| 8. Workflow Automation | `routers/dashboard.py` → `/expiring-contracts` (hook to a cron + email/SMS) |
| 9. Incident Intelligence | `routers/dashboard.py` → `/incident-intelligence` |
| 10. Dashboard | `frontend/index.html` + `app.js` (Chart.js) + `routers/dashboard.py` |

## Next steps to extend (post-MVP, if you have time)

- **Auth/roles:** add login so only "higher authority" can view sensitive categories (Legal/Finance) — use FastAPI's OAuth2 + a `role` column on a Users table.
- **Real reminders:** wire `/expiring-contracts` to `APScheduler` + an SMTP email sender that runs daily.
- **Better OCR for tables:** for scanned tender tables, consider `unstructured` or `layoutparser` instead of raw pytesseract.
- **PDF viewer with highlight:** when assistant cites a source, deep-link to the exact page using PyMuPDF's page search.
- **Multi-file batch upload:** loop the same `/upload` endpoint client-side.
- **Deploy:** backend on Render/Railway (free tier), frontend on Vercel/Netlify, swap SQLite for Postgres if you want persistence beyond a demo.

## Demo talking points for judges

- Point at the **architecture diagram** above and literally read the RAG pipeline out loud — it's exactly what you listed in your spec.
- Show a **before/after**: "earlier, finding a signalling fault meant opening 200 PDFs and Ctrl+F. Now it's one sentence."
- Show the **duplicate detection** catching `Tender_v2` vs `Tender_Final`.
- Show the **incident intelligence** insight line — this is the "wow" feature, looks the most like real AI reasoning.
