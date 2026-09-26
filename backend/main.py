"""
Entry point. Run with:
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import upload, search, assistant, dashboard

app = FastAPI(title="Kochi Metro Document Intelligence AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(upload.router)
app.include_router(search.router)
app.include_router(assistant.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "Kochi Metro AI backend running", "docs": "/docs"}
