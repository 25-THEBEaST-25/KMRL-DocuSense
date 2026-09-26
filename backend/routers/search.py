"""
Feature 2: Natural Language Search.
"Which stations had signalling failures in July?" -> semantic search
over vector DB, optionally filtered by structured metadata.
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Query
from vectorstore import search as vector_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search_documents(q: str = Query(..., description="Natural language query"),
                      category: str = None,
                      top_k: int = 8):
    where = {"category": category} if category else None
    results = vector_search(q, top_k=top_k, where=where)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for text, meta, dist in zip(docs, metas, distances):
        hits.append({
            "text_snippet": text[:300],
            "filename": meta.get("filename"),
            "category": meta.get("category"),
            "station": meta.get("station"),
            "doc_id": meta.get("doc_id"),
            "relevance_score": round(1 - dist, 3),  # cosine distance -> similarity
        })

    return {"query": q, "results": hits}
