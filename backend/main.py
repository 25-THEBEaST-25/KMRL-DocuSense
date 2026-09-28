"""
Entry point. Run with:
    uvicorn main:app --reload --port 8000
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import upload, search, assistant, dashboard

_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()]

app = FastAPI(title="Kochi Metro Document Intelligence AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

init_db()

app.include_router(upload.router)
app.include_router(search.router)
app.include_router(assistant.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "Kochi Metro AI backend running", "docs": "/docs"}
