"""
OCR + text extraction.
Step 1 of the pipeline: PDF/Image -> raw text.

Uses PyMuPDF first (fast, works for text-based PDFs).
Falls back to pytesseract OCR for scanned/image-only PDFs.
"""
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os


def extract_text_from_pdf(filepath: str) -> str:
    """Try native text extraction first; OCR only pages that come back empty."""
    text_parts = []
    doc = fitz.open(filepath)

    needs_ocr_pages = []
    for i, page in enumerate(doc):
        page_text = page.get_text().strip()
        if len(page_text) > 20:
            text_parts.append(page_text)
        else:
            text_parts.append(None)  # placeholder, will OCR this page
            needs_ocr_pages.append(i)
    doc.close()

    if needs_ocr_pages:
        images = convert_from_path(filepath)
        for i in needs_ocr_pages:
            if i < len(images):
                ocr_text = pytesseract.image_to_string(images[i])
                text_parts[i] = ocr_text

    return "\n".join([t for t in text_parts if t])


def extract_text_from_image(filepath: str) -> str:
    img = Image.open(filepath)
    return pytesseract.image_to_string(img)


def extract_text(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return extract_text_from_image(filepath)
    elif ext == ".txt":
        with open(filepath, "r", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")
