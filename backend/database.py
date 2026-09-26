"""
SQLite database layer. Stores STRUCTURED metadata about every document
(the fields the AI extracts). The actual text chunks + embeddings live
in ChromaDB (see vectorstore.py) — this DB is for fast filtering,
dashboards, and the fields shown in search results.
"""
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.getenv("SQLITE_PATH", "../data/kochi_metro.db")
engine = create_engine(f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    # AI-classified
    category = Column(String, index=True)       # Maintenance / Legal / Finance / Tender / etc.
    tags = Column(String)                        # comma separated extra tags

    # AI-extracted structured fields (nullable — not every doc has every field)
    doc_date = Column(String, index=True)         # date mentioned in the document
    station = Column(String, index=True)
    equipment = Column(String, index=True)
    engineer = Column(String)
    fault = Column(String)
    severity = Column(String, index=True)         # Low / Medium / High / Critical
    resolution = Column(Text)
    vendor = Column(String)
    contract_expiry = Column(String, index=True)  # for tender/vendor docs
    amount = Column(String)

    summary = Column(Text)                        # short AI summary of the doc
    raw_text_preview = Column(Text)                # first ~1000 chars (debug/search context)

    # duplicate detection
    content_hash = Column(String, index=True)
    is_duplicate_of = Column(Integer, nullable=True)

    # workflow
    reviewed = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)


def init_db():
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
