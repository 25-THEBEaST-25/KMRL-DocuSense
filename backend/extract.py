"""
Feature 1: AI Document Understanding.
Given raw OCR'd text, ask the LLM to pull out structured fields
(Date, Station, Equipment, Engineer, Fault, Severity, Resolution etc.)
This is what replaces "just storing a PDF" with an actual structured record.
"""
import re

from llm import chat_json, LLM_ENABLED

EXTRACTION_SYSTEM_PROMPT = """You are a document intelligence system for Kochi Metro Rail Limited (KMRL).
You will be given raw text extracted from an internal document (maintenance report,
tender, vendor contract, incident report, HR doc, etc).

Extract the following as a single JSON object. If a field is not present in the
document, use null. Do NOT invent information.

Fields:
- "category": one of ["Maintenance", "Legal", "Finance", "Tender", "Vendor", "Operations", "Safety", "HR", "Other"]
- "doc_date": the main date mentioned (format YYYY-MM-DD if possible, else as written), or null
- "station": station name if mentioned, or null
- "equipment": equipment/system name if mentioned (e.g. "Signalling System", "Brake Unit"), or null
- "engineer": person responsible / author, or null
- "fault": short description of the fault/issue if this is a maintenance/incident doc, or null
- "severity": one of ["Low", "Medium", "High", "Critical"] if applicable, or null
- "resolution": how the issue was resolved, or null
- "vendor": vendor/contractor name if applicable, or null
- "contract_expiry": contract/tender expiry date if applicable (YYYY-MM-DD), or null
- "amount": monetary amount mentioned if applicable, or null
- "tags": array of 2-5 short relevant keyword tags
- "summary": a 2-3 sentence plain-English summary of the document

Return ONLY the JSON object, nothing else.
"""


def extract_fields(document_text: str) -> dict:
    # Truncate very long docs — first ~6000 chars usually carries the key metadata
    truncated = document_text[:6000]
    if LLM_ENABLED:
        return chat_json(EXTRACTION_SYSTEM_PROMPT, truncated)

    lines = [line.strip() for line in truncated.splitlines() if line.strip()]
    date_match = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", truncated)
    severity_match = re.search(r"\b(low|medium|high|critical)\b", truncated, re.IGNORECASE)
    summary = " ".join(lines[:2])[:500] if lines else "Document uploaded without LLM extraction."
    return {
        "category": "Other",
        "doc_date": date_match.group(1) if date_match else None,
        "station": None,
        "equipment": None,
        "engineer": None,
        "fault": None,
        "severity": severity_match.group(1).title() if severity_match else None,
        "resolution": None,
        "vendor": None,
        "contract_expiry": None,
        "amount": None,
        "tags": [],
        "summary": summary,
    }
