# Production Readiness — DocuSense AI

This repo meets the production-readiness bar: it can be cloned, run, understood, and trusted by another engineer without hand-holding.

## Checklist

- [x] `docs/architecture.md` — RAG pipeline diagram, tech stack, data flow from PDF to answer
- [x] `docs/setup.md` — step-by-step install, seed, run, and API endpoint reference
- [x] `docker-compose.yml` — single-command backend + frontend startup
- [x] Input validation on upload routes — file size limit (`MAX_UPLOAD_SIZE_MB`), allowed extensions/MIME types, path-traversal-safe filenames (`backend/upload_validation.py`, covered by `backend/tests/test_upload_validation.py`)
- [x] README badges — CI status, Python version, license
- [x] `.env.example` covers all env vars used by the backend and docker-compose (`ALLOWED_ORIGINS`, `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`, `SQLITE_PATH`, `CHROMA_DIR`, `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`)
- [x] `LICENSE` (MIT), referenced by the README badge
- [x] CI (`.github/workflows/ci.yml`) green on `main` — backend compile/import checks, unit tests, frontend HTML lint
- [x] GitHub Pages deploy workflow (`.github/workflows/pages.yml`) — live interactive demo

## Verified

- `python -m pytest backend/tests -v` — 7/7 passed
- `python -c "import main"` from `backend/` — imports cleanly with `pip install -r backend/requirements.txt`
- CI green on `main` at commit `60eb47a` (both the `CI` and `Deploy Demo to GitHub Pages` workflows)

## Known limitations (acceptable, not blockers)

- Demo dataset (`seed_db.py`) is synthetic KMRL-style data, not real operational documents.
- OCR pipeline (Tesseract) is untested against low-quality scans; accuracy will vary with real-world document quality.
