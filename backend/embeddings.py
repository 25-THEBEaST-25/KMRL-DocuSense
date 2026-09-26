"""
Step 3 of the pipeline: text -> vector embeddings.
Uses a local sentence-transformers model — no API cost, works offline.
"""
from sentence_transformers import SentenceTransformer
from typing import List

_model = None


def get_model():
    global _model
    if _model is None:
        # small, fast, good quality-for-size. ~80MB download on first run.
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]
