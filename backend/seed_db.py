"""
KMRL SIH Demo Seed Script
=========================
Populates BOTH SQLite (structured metadata) AND ChromaDB (embeddings) with
80+ realistic Kochi Metro Rail Limited documents so every dashboard feature
works on first demo without uploading a single file.

Run from the backend directory:
    python seed_db.py
    # or, to wipe and re-seed:
    python seed_db.py --reset
"""
import argparse
import os
import sys
import hashlib
from datetime import datetime, timedelta
import random

# ── make sure imports resolve when run from backend/ ──────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import init_db, SessionLocal, Document
from vectorstore import get_collection
from embeddings import embed_texts

random.seed(42)

# ── KMRL domain data ───────────────────────────────────────────────────────────
STATIONS = [
    "Aluva", "Pulinchodu", "Companypady", "Ambattukavu", "Muttom",
    "Kalamassery", "CUSAT", "Pathadipalam", "Edapally", "Changampuzha Park",
    "Palarivattom", "JLN Stadium", "Kaloor", "Town Hall", "MG Road",
    "Maharaja's College", "Ernakulam South", "Kadavanthra", "Elamkulam",
    "Vyttila", "Thaikoodam", "Kundannoor", "SN Junction", "Tripunithura",
]

EQUIPMENT = [
    "Signalling System", "Brake Unit", "Door Mechanism", "HVAC Unit",
    "Platform Screen Doors", "Escalator", "Elevator", "Traction System",
    "Communication System", "Overhead Equipment", "Track Circuit",
    "Fire Detection System", "CCTV System", "AFC Ticketing Machine",
    "Automatic Train Protection", "Radio Block Centre",
]

ENGINEERS = [
    "R. Krishnamurthy", "S. Anand", "P. Nair", "A. Menon", "V. Suresh",
    "K. Thomas", "M. Rajan", "B. Pillai", "D. Varghese", "L. Iyer",
    "F. George", "H. Mohan", "J. Sabu", "N. Chandran", "Q. Babu",
]

VENDORS = [
    "Alstom India Ltd", "Siemens Mobility", "BEML Limited",
    "Tata Projects Ltd", "L&T Infrastructure", "Thales Group India",
    "Knorr-Bremse India", "Faiveley Transport India", "ABB India Ltd",
    "Hitachi Rail India", "CAF India Pvt Ltd", "DB Engineering India",
]

FAULTS = [
    "Brake Failure", "Door Malfunction", "Signalling Error",
    "HVAC Failure", "Escalator Breakdown", "Communication Failure",
    "Power Supply Fault", "Track Circuit Failure", "PSD Jam",
    "Traction Motor Fault", "OHE Voltage Drop", "AFC Machine Jam",
    "Fire Alarm False Trigger", "CCTV Offline",
]

RESOLUTIONS = [
    "Brake pads replaced and system recalibrated; test run completed.",
    "Door sensor cleaned and realigned; closure test passed.",
    "Signal controller firmware updated; normal operations resumed.",
    "HVAC filter replaced and refrigerant topped up; temperature stable.",
    "Escalator motor bearing replaced; load test completed.",
    "Radio module swapped; communication link restored.",
    "UPS replaced and power restored within 45 minutes.",
    "Track circuit relay cleaned and contact tightened; train detection normal.",
    "PSD rail lubricated and obstruction cleared; full cycle test OK.",
    "Traction motor winding repaired; dynamic brake test passed.",
    "OHE tension adjusted and pantograph contact improved.",
    "Ticket machine jam cleared; paper roll replaced.",
    "Smoke detector replaced; false alarm root cause identified as dust.",
    "CCTV DVR rebooted and network cable replaced.",
]

# ── document templates ─────────────────────────────────────────────────────────
def date_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

def date_future(days: int) -> str:
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")


def make_maintenance_doc(i: int) -> dict:
    station = random.choice(STATIONS)
    equip = random.choice(EQUIPMENT)
    fault = random.choice(FAULTS)
    engineer = random.choice(ENGINEERS)
    severity = random.choices(
        ["Low", "Medium", "High", "Critical"],
        weights=[30, 40, 20, 10], k=1
    )[0]
    days_ago = random.randint(1, 90)
    doc_date = date_ago(days_ago)
    resolution = random.choice(RESOLUTIONS)
    text = (
        f"KMRL MAINTENANCE REPORT\n"
        f"Report No: MR-2026-{1000+i}\n"
        f"Date: {doc_date}\n"
        f"Station: {station}\n"
        f"Equipment: {equip}\n"
        f"Engineer-in-charge: {engineer}\n\n"
        f"Issue Description:\n"
        f"{fault} reported at {station} station during routine inspection. "
        f"Severity assessed as {severity}. Immediate corrective action was initiated "
        f"by the maintenance team under {engineer}.\n\n"
        f"Root Cause Analysis:\n"
        f"The {equip} at {station} showed signs of wear consistent with extended "
        f"operational hours. Environmental factors (humidity, dust) contributed to "
        f"accelerated degradation.\n\n"
        f"Resolution:\n"
        f"{resolution}\n\n"
        f"Status: Closed\n"
        f"Next scheduled inspection: {date_future(random.randint(30, 180))}\n"
    )
    return {
        "filename": f"maintenance_report_{station.replace(' ','_').replace(chr(39),'')}_MR{1000+i}.pdf",
        "category": "Maintenance",
        "tags": f"maintenance,{fault.lower().replace(' ','-')},{station.lower().replace(' ','-')}",
        "doc_date": doc_date,
        "station": station,
        "equipment": equip,
        "engineer": engineer,
        "fault": fault,
        "severity": severity,
        "resolution": resolution,
        "vendor": None,
        "contract_expiry": None,
        "amount": None,
        "summary": (
            f"Maintenance report for {fault} at {station} station ({equip}). "
            f"Severity: {severity}. Filed by {engineer} on {doc_date}. Issue resolved."
        ),
        "raw_text": text,
    }


def make_incident_doc(i: int) -> dict:
    station = random.choice(STATIONS)
    fault = random.choice(FAULTS)
    engineer = random.choice(ENGINEERS)
    severity = random.choices(["Medium", "High", "Critical"], weights=[40, 40, 20], k=1)[0]
    days_ago = random.randint(1, 60)
    doc_date = date_ago(days_ago)
    text = (
        f"KMRL INCIDENT REPORT\n"
        f"Incident Ref: IR-2026-{2000+i}\n"
        f"Date & Time: {doc_date} {random.randint(6,22):02d}:{random.choice(['00','15','30','45'])}\n"
        f"Station: {station}\n"
        f"Reported By: {engineer}\n"
        f"Severity: {severity}\n\n"
        f"Incident Summary:\n"
        f"A {fault} incident occurred at {station} during peak-hour operations. "
        f"Approximately {random.randint(50,400)} passengers were affected. "
        f"Service disruption lasted {random.randint(5,45)} minutes.\n\n"
        f"Immediate Actions Taken:\n"
        f"1. Emergency protocol activated at {station}.\n"
        f"2. Passengers evacuated/redirected via adjacent platforms.\n"
        f"3. Technical team dispatched within {random.randint(5,20)} minutes.\n\n"
        f"Follow-up Actions Required:\n"
        f"- Detailed root cause analysis within 72 hours.\n"
        f"- Equipment overhaul scheduled for next maintenance window.\n"
        f"- Staff debriefing and SOP review to be conducted.\n"
    )
    return {
        "filename": f"incident_report_IR{2000+i}_{station.replace(' ','_').replace(chr(39),'')}.pdf",
        "category": "Safety",
        "tags": f"incident,safety,{severity.lower()},{station.lower().replace(' ','-')}",
        "doc_date": doc_date,
        "station": station,
        "equipment": None,
        "engineer": engineer,
        "fault": fault,
        "severity": severity,
        "resolution": "Investigation in progress; corrective actions logged.",
        "vendor": None,
        "contract_expiry": None,
        "amount": None,
        "summary": (
            f"Incident report for {fault} at {station} station. "
            f"Severity {severity}. Reported by {engineer} on {doc_date}. "
            f"Corrective actions initiated."
        ),
        "raw_text": text,
    }


def make_tender_doc(i: int) -> dict:
    vendor = random.choice(VENDORS)
    amount = f"₹{random.randint(50,500):,}.{random.randint(10,99)} Lakhs"
    # first 6 tenders expire soon (powers the expiring-contracts demo feature)
    days_till_expiry = random.randint(5, 28) if i < 6 else random.randint(45, 365)
    contract_expiry = date_future(days_till_expiry)
    doc_date = date_ago(random.randint(30, 365))
    tender_type = random.choice([
        "Supply of Rolling Stock Spares", "Track Maintenance Contract",
        "Station Housekeeping Services", "Signalling System Upgrade",
        "CCTV Surveillance System", "Escalator AMC", "Elevator AMC",
        "IT Infrastructure Services", "Security Services Contract",
        "Electrical Maintenance", "Civil Works Contract",
    ])
    text = (
        f"KMRL TENDER / CONTRACT DOCUMENT\n"
        f"Tender Ref: TDR-2026-{3000+i}\n"
        f"Date: {doc_date}\n"
        f"Subject: {tender_type}\n"
        f"Vendor: {vendor}\n"
        f"Contract Value: {amount}\n"
        f"Contract Expiry: {contract_expiry}\n\n"
        f"Scope of Work:\n"
        f"This contract covers {tender_type.lower()} for Kochi Metro Rail Limited "
        f"across all designated stations and depot facilities. The vendor ({vendor}) "
        f"is responsible for maintaining performance standards as per KMRL SLA.\n\n"
        f"Terms & Conditions:\n"
        f"- Performance bank guarantee: 10% of contract value\n"
        f"- Payment: Quarterly upon submission of bills\n"
        f"- Penalty: 0.5% per week for SLA breach\n"
        f"- Renewal subject to satisfactory performance review\n\n"
        f"Authorized by: Managing Director, KMRL\n"
    )
    return {
        "filename": f"tender_{tender_type.replace(' ','_')[:30]}_TDR{3000+i}.pdf",
        "category": "Tender",
        "tags": f"tender,contract,{vendor.split()[0].lower()},procurement",
        "doc_date": doc_date,
        "station": None,
        "equipment": None,
        "engineer": None,
        "fault": None,
        "severity": None,
        "resolution": None,
        "vendor": vendor,
        "contract_expiry": contract_expiry,
        "amount": amount,
        "summary": (
            f"Tender/contract for {tender_type} with {vendor}. "
            f"Value: {amount}. Expires: {contract_expiry}."
        ),
        "raw_text": text,
    }


def make_operations_doc(i: int) -> dict:
    station = random.choice(STATIONS)
    doc_date = date_ago(random.randint(1, 30))
    ridership = random.randint(8000, 45000)
    text = (
        f"KMRL DAILY OPERATIONS REPORT\n"
        f"Report No: OPS-2026-{4000+i}\n"
        f"Date: {doc_date}\n"
        f"Station: {station}\n\n"
        f"Ridership Summary:\n"
        f"Total footfall: {ridership:,} passengers\n"
        f"Peak hour (08:00-10:00): {int(ridership*0.35):,}\n"
        f"Off-peak: {int(ridership*0.65):,}\n\n"
        f"Train Operations:\n"
        f"Scheduled trips: {random.randint(80,140)}\n"
        f"Operated trips: {random.randint(78,140)}\n"
        f"Punctuality: {random.randint(94,100)}%\n\n"
        f"Revenue:\n"
        f"Fare collection: ₹{random.randint(60,250):,},000\n"
        f"Monthly cumulative: ₹{random.randint(1,8):,},00,000\n\n"
        f"Remarks: Operations normal. No major disruptions reported.\n"
    )
    return {
        "filename": f"operations_report_{station.replace(' ','_').replace(chr(39),'')}_OPS{4000+i}.pdf",
        "category": "Operations",
        "tags": f"operations,ridership,revenue,{station.lower().replace(' ','-')}",
        "doc_date": doc_date,
        "station": station,
        "equipment": None,
        "engineer": random.choice(ENGINEERS),
        "fault": None,
        "severity": None,
        "resolution": None,
        "vendor": None,
        "contract_expiry": None,
        "amount": f"₹{random.randint(60,250):,},000",
        "summary": (
            f"Daily operations report for {station} station dated {doc_date}. "
            f"Ridership: {ridership:,} passengers. Normal operations."
        ),
        "raw_text": text,
    }


def make_finance_doc(i: int) -> dict:
    doc_date = date_ago(random.randint(1, 90))
    quarter = random.choice(["Q1", "Q2", "Q3", "Q4"])
    revenue = random.randint(120, 400)
    expenses = random.randint(90, revenue - 10)
    text = (
        f"KMRL FINANCIAL REPORT\n"
        f"Ref: FIN-2026-{5000+i}\n"
        f"Date: {doc_date}\n"
        f"Period: {quarter} FY 2025-26\n\n"
        f"Revenue Summary:\n"
        f"Fare Revenue: ₹{revenue} Cr\n"
        f"Non-Fare Revenue: ₹{random.randint(5,30)} Cr\n"
        f"Total Revenue: ₹{revenue + random.randint(5,30)} Cr\n\n"
        f"Expenditure:\n"
        f"Operations & Maintenance: ₹{expenses} Cr\n"
        f"Staff Costs: ₹{random.randint(20,50)} Cr\n"
        f"Debt Servicing: ₹{random.randint(30,80)} Cr\n\n"
        f"Net Surplus/(Deficit): ₹{revenue - expenses} Cr\n\n"
        f"Key Observations:\n"
        f"- Ridership grew {random.randint(3,18)}% YoY\n"
        f"- Energy costs up {random.randint(2,10)}% due to tariff revision\n"
        f"- EBIDTA margins at {random.randint(18,35)}%\n"
    )
    return {
        "filename": f"financial_report_{quarter}_FIN{5000+i}.pdf",
        "category": "Finance",
        "tags": f"finance,revenue,{quarter.lower()},quarterly",
        "doc_date": doc_date,
        "station": None,
        "equipment": None,
        "engineer": None,
        "fault": None,
        "severity": None,
        "resolution": None,
        "vendor": None,
        "contract_expiry": None,
        "amount": f"₹{revenue} Cr",
        "summary": (
            f"Financial report for {quarter} FY 2025-26. "
            f"Fare revenue ₹{revenue} Cr. Net surplus ₹{revenue - expenses} Cr."
        ),
        "raw_text": text,
    }


def make_hr_doc(i: int) -> dict:
    doc_date = date_ago(random.randint(1, 180))
    employee = random.choice(ENGINEERS)
    doc_types = [
        ("Appointment Letter", "appointment"),
        ("Performance Appraisal", "appraisal"),
        ("Transfer Order", "transfer"),
        ("Training Completion Certificate", "training"),
    ]
    dtype, tag = random.choice(doc_types)
    text = (
        f"KMRL HR DOCUMENT\n"
        f"Document Type: {dtype}\n"
        f"Ref: HR-2026-{6000+i}\n"
        f"Date: {doc_date}\n"
        f"Employee: {employee}\n"
        f"Department: {random.choice(['Operations', 'Maintenance', 'Finance', 'Administration'])}\n\n"
        f"Dear {employee},\n\n"
        f"This is to confirm that your {dtype.lower()} has been processed "
        f"as per the personnel records of Kochi Metro Rail Limited. "
        f"Please retain this document for your personal records.\n\n"
        f"This document is issued by the Human Resources Department, KMRL.\n"
    )
    return {
        "filename": f"hr_{tag}_{employee.replace(' ','_').replace('.','')}_HR{6000+i}.pdf",
        "category": "HR",
        "tags": f"hr,{tag},personnel,{employee.split()[0].lower()}",
        "doc_date": doc_date,
        "station": None,
        "equipment": None,
        "engineer": employee,
        "fault": None,
        "severity": None,
        "resolution": None,
        "vendor": None,
        "contract_expiry": None,
        "amount": None,
        "summary": f"HR {dtype} for {employee} dated {doc_date}. Issued by KMRL Human Resources.",
        "raw_text": text,
    }


# ── build full record list ─────────────────────────────────────────────────────
def build_records() -> list[dict]:
    records = []
    # Maintenance (35) — heavy on faults for trend detection
    for i in range(35):
        records.append(make_maintenance_doc(i))
    # Safety/Incidents (18)
    for i in range(18):
        records.append(make_incident_doc(i))
    # Tender/Vendor (15) — some expiring soon
    for i in range(15):
        records.append(make_tender_doc(i))
    # Operations (12)
    for i in range(12):
        records.append(make_operations_doc(i))
    # Finance (8)
    for i in range(8):
        records.append(make_finance_doc(i))
    # HR (7)
    for i in range(7):
        records.append(make_hr_doc(i))
    return records


# ── seeding ────────────────────────────────────────────────────────────────────
def seed(reset: bool = False):
    init_db()
    db = SessionLocal()

    if reset:
        print("Resetting existing records…")
        db.query(Document).delete()
        db.commit()
        # also clear chroma
        try:
            col = get_collection()
            existing = col.get()
            if existing["ids"]:
                col.delete(ids=existing["ids"])
                print(f"  Cleared {len(existing['ids'])} vectors from ChromaDB.")
        except Exception as e:
            print(f"  ChromaDB clear warning: {e}")

    existing_count = db.query(Document).count()
    if existing_count > 0 and not reset:
        print(f"Database already has {existing_count} records. Run with --reset to re-seed.")
        db.close()
        return

    records = build_records()
    print(f"Seeding {len(records)} documents…")

    col = get_collection()
    batch_texts, batch_metas, batch_ids = [], [], []

    for idx, r in enumerate(records):
        content_hash = hashlib.md5(r["raw_text"].encode()).hexdigest()

        doc = Document(
            filename=r["filename"],
            filepath=f"../data/seeded/{r['filename']}",
            upload_date=datetime.utcnow() - timedelta(days=random.randint(0, 89)),
            category=r["category"],
            tags=r["tags"],
            doc_date=r["doc_date"],
            station=r.get("station"),
            equipment=r.get("equipment"),
            engineer=r.get("engineer"),
            fault=r.get("fault"),
            severity=r.get("severity"),
            resolution=r.get("resolution"),
            vendor=r.get("vendor"),
            contract_expiry=r.get("contract_expiry"),
            amount=r.get("amount"),
            summary=r["summary"],
            raw_text_preview=r["raw_text"][:1000],
            content_hash=content_hash,
            is_duplicate_of=None,
            reviewed=random.choice([True, False]),
            reminder_sent=False,
        )
        db.add(doc)
        db.flush()  # get doc.id without full commit

        # queue for vector batch
        chunk = r["raw_text"][:800]  # one chunk per seeded doc
        batch_texts.append(chunk)
        batch_metas.append({
            "filename": r["filename"],
            "category": r["category"],
            "station": r.get("station") or "",
            "doc_id": doc.id,
            "chunk_index": 0,
        })
        batch_ids.append(f"seed_doc{doc.id}_chunk0")

        if (idx + 1) % 10 == 0:
            print(f"  [{idx+1}/{len(records)}] records staged…")

    db.commit()
    print("SQLite commit done.")

    # embed and store in ChromaDB
    print(f"Generating embeddings for {len(batch_texts)} chunks (sentence-transformers)…")
    embeddings = embed_texts(batch_texts)
    col.add(
        ids=batch_ids,
        embeddings=embeddings,
        documents=batch_texts,
        metadatas=batch_metas,
    )
    print("ChromaDB vectors stored.")

    db.close()

    # summary
    final_db = SessionLocal()
    total = final_db.query(Document).count()
    from collections import Counter
    cats = Counter(d.category for d in final_db.query(Document).all())
    final_db.close()

    print(f"\n✓ Seed complete — {total} documents in SQLite + {len(batch_ids)} vectors in ChromaDB")
    print("  Category breakdown:")
    for cat, cnt in sorted(cats.items()):
        print(f"    {cat:<15} {cnt}")
    print("\nRun the backend: cd backend && uvicorn main:app --reload")
    print("Then open the frontend or hit http://localhost:8000/api/dashboard/stats")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed KMRL demo database for SIH")
    parser.add_argument("--reset", action="store_true", help="Wipe existing data before seeding")
    args = parser.parse_args()
    seed(reset=args.reset)
