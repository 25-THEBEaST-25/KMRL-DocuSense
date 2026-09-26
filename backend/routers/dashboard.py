"""
Feature 9: Incident Intelligence + Feature 10: Dashboard + Feature 8: Workflow automation.
"""
import os, sys
from datetime import datetime, timedelta
from collections import Counter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dateutil import parser as dateparser

from database import get_db, Document

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    all_docs = db.query(Document).all()
    today = datetime.utcnow().date()

    total = len(all_docs)
    today_uploads = sum(1 for d in all_docs if d.upload_date and d.upload_date.date() == today)
    pending_review = sum(1 for d in all_docs if not d.reviewed)

    category_counts = Counter(d.category or "Uncategorized" for d in all_docs)
    fault_counts = Counter(d.fault for d in all_docs if d.fault)
    station_counts = Counter(d.station for d in all_docs if d.station)
    severity_counts = Counter(d.severity for d in all_docs if d.severity)

    return {
        "total_documents": total,
        "today_uploads": today_uploads,
        "pending_reviews": pending_review,
        "department_wise": dict(category_counts),
        "most_common_faults": fault_counts.most_common(10),
        "station_wise": dict(station_counts),
        "severity_breakdown": dict(severity_counts),
    }


@router.get("/incident-intelligence")
def incident_intelligence(db: Session = Depends(get_db)):
    """
    Feature 9: notices trends like 'Brake Failure has increased 42%'
    by comparing fault frequency this month vs last month.
    """
    all_docs = db.query(Document).filter(Document.fault.isnot(None)).all()
    now = datetime.utcnow()
    this_month_start = now.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_month_faults, last_month_faults = Counter(), Counter()

    for d in all_docs:
        if not d.doc_date:
            continue
        try:
            dt = dateparser.parse(d.doc_date, fuzzy=True)
        except Exception:
            continue
        if dt >= this_month_start:
            this_month_faults[d.fault] += 1
        elif last_month_start <= dt < this_month_start:
            last_month_faults[d.fault] += 1

    insights = []
    for fault, count in this_month_faults.items():
        prev = last_month_faults.get(fault, 0)
        if prev > 0:
            change_pct = round(((count - prev) / prev) * 100, 1)
            if abs(change_pct) >= 20:  # only surface meaningful trends
                direction = "increased" if change_pct > 0 else "decreased"
                insights.append(f"'{fault}' has {direction} {abs(change_pct)}% compared to last month.")
        elif count >= 3:
            insights.append(f"New recurring issue detected: '{fault}' reported {count} times this month.")

    return {"insights": insights, "this_month": dict(this_month_faults), "last_month": dict(last_month_faults)}


@router.get("/expiring-contracts")
def expiring_contracts(days: int = 30, db: Session = Depends(get_db)):
    """
    Feature 8: Workflow automation — surfaces contracts/tenders expiring
    within `days`. Hook this up to a cron job + email/SMS to actually
    "automatically remind Procurement".
    """
    docs = db.query(Document).filter(Document.contract_expiry.isnot(None)).all()
    now = datetime.utcnow()
    soon = now + timedelta(days=days)

    expiring = []
    for d in docs:
        try:
            expiry_date = dateparser.parse(d.contract_expiry, fuzzy=True)
        except Exception:
            continue
        if now <= expiry_date <= soon:
            expiring.append({
                "id": d.id,
                "filename": d.filename,
                "vendor": d.vendor,
                "contract_expiry": d.contract_expiry,
                "days_remaining": (expiry_date - now).days,
            })

    expiring.sort(key=lambda x: x["days_remaining"])
    return {"expiring_contracts": expiring}
