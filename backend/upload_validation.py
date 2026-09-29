"""
Upload validation. Kept dependency-free (no OCR/ML imports) so it can be
unit tested in isolation and in CI without installing the heavy pipeline
packages.
"""
import os

from fastapi import HTTPException

# Kept in sync with the formats ocr.extract_text() knows how to read.
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "image/bmp",
    "text/plain",
}


def safe_filename(filename: str) -> str:
    """Strip any directory components and reject names that can't map to
    a real file on disk, so a crafted filename (e.g. "../../etc/passwd")
    can't be used to write or read outside UPLOAD_DIR."""
    name = os.path.basename((filename or "").strip())
    if not name or name in (".", ".."):
        raise HTTPException(400, "Invalid filename.")
    return name


def validate_upload(filename: str, content_type: str | None) -> str:
    """Validate a candidate upload's filename and content type.
    Returns the sanitized filename to store on disk, or raises HTTPException."""
    name = safe_filename(filename)
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type '{ext or 'unknown'}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported content type '{content_type}'.")
    return name


def max_upload_size_bytes() -> int:
    return int(os.getenv("MAX_UPLOAD_SIZE_MB", "20")) * 1024 * 1024
