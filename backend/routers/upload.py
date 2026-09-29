"""
Upload endpoint. This wires together the ENTIRE pipeline:
File -> OCR -> Extraction -> Classification -> Chunking -> Embedding
-> Vector DB + SQLite -> Duplicate check
"""
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, Document
from ocr import extract_text
from extract import extract_fields
from chunking import chunk_text
from vectorstore import add_chunks
from duplicate import compute_hash, find_duplicate
from upload_validation import validate_upload, max_upload_size_bytes

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../data/uploads")

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    safe_filename = validate_upload(file.filename, file.content_type)
    max_size = max_upload_size_bytes()

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, safe_filename)

    size = 0
    try:
        with open(filepath, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(
                        413,
                        f"File too large. Max size is {max_size // (1024 * 1024)}MB.",
                    )
                f.write(chunk)
    except HTTPException:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise

    file.filename = safe_filename

    # 1. OCR / text extraction
    try:
        raw_text = extract_text(filepath)
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    if not raw_text.strip():
        raise HTTPException(400, "No readable text found in document (bad scan?).")

    # 2. Duplicate detection (before we waste an LLM call)
    content_hash = compute_hash(raw_text)
    dup_doc, score = find_duplicate(db, file.filename, content_hash, raw_text[:1000])

    # 3. AI extraction (structured fields + classification + summary)
    fields = extract_fields(raw_text)

    doc = Document(
        filename=file.filename,
        filepath=filepath,
        category=fields.get("category"),
        tags=",".join(fields.get("tags") or []),
        doc_date=fields.get("doc_date"),
        station=fields.get("station"),
        equipment=fields.get("equipment"),
        engineer=fields.get("engineer"),
        fault=fields.get("fault"),
        severity=fields.get("severity"),
        resolution=fields.get("resolution"),
        vendor=fields.get("vendor"),
        contract_expiry=fields.get("contract_expiry"),
        amount=fields.get("amount"),
        summary=fields.get("summary"),
        raw_text_preview=raw_text[:1000],
        content_hash=content_hash,
        is_duplicate_of=dup_doc.id if dup_doc else None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 4. Chunk + embed + store in vector DB (skip if it's a near-duplicate)
    if not dup_doc:
        chunks = chunk_text(raw_text)
        add_chunks(
            doc.id,
            chunks,
            metadata={
                "filename": doc.filename,
                "category": doc.category or "Other",
                "station": doc.station or "",
            },
        )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "category": doc.category,
        "summary": doc.summary,
        "extracted_fields": fields,
        "duplicate_of": {"id": dup_doc.id, "filename": dup_doc.filename, "score": score} if dup_doc else None,
    }


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return {c.name: getattr(doc, c.name) for c in doc.__table__.columns}


@router.get("")
def list_documents(category: str = None, station: str = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if category:
        query = query.filter(Document.category == category)
    if station:
        query = query.filter(Document.station == station)
    docs = query.order_by(Document.upload_date.desc()).all()
    return [{c.name: getattr(d, c.name) for c in d.__table__.columns} for d in docs]
