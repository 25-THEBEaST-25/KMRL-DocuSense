"""
Step 2 of the pipeline: split raw text into overlapping chunks
small enough to embed well and retrieve precisely.
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """
    Simple sliding-window chunker on characters (works fine for
    hackathon scale; swap for a token-based splitter later if needed).
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks
