"""
Feature 7: Duplicate Detection.
Two layers:
1. Exact content hash match (catches re-uploads of the identical file).
2. Fuzzy filename + text-similarity match (catches "Tender_v2" vs
   "Tender_Final" vs "Tender_Final_Last" style near-duplicates).
"""
import hashlib
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from database import Document


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def find_duplicate(db: Session, filename: str, content_hash: str, text_preview: str):
    """
    Returns the Document row this upload duplicates, or None.
    """
    # 1. exact content match
    exact = db.query(Document).filter(Document.content_hash == content_hash).first()
    if exact:
        return exact, 100.0

    # 2. fuzzy match against filenames + preview text of existing docs
    candidates = db.query(Document).all()
    best_match, best_score = None, 0.0
    for doc in candidates:
        name_score = fuzz.token_sort_ratio(filename, doc.filename)
        text_score = fuzz.token_sort_ratio(text_preview[:500], (doc.raw_text_preview or "")[:500])
        combined = 0.4 * name_score + 0.6 * text_score
        if combined > best_score:
            best_match, best_score = doc, combined

    if best_score >= 85:  # tune threshold as needed
        return best_match, best_score

    return None, 0.0
