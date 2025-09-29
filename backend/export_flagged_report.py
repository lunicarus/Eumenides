import asyncio
import csv
from app.infra.sql_repository import SqlAccountRepository
from app.domain.entities import FlaggedAccount
from app.domain.value_objects import Timestamp
from datetime import datetime
import json

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

async def export_flagged_to_csv(csv_path="flagged_accounts_report.csv"):
    repo = SqlAccountRepository()
    flagged = await repo.list_flagged(limit=1000)
    with open(csv_path, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Platform", "Handle", "Display Name", "Description", "Participants", "Risk Score", "Reasons", "First Seen", "Last Seen"
        ])
        for acc in flagged:
            meta = acc.metadata
            writer.writerow([
                acc.id,
                meta.platform,
                meta.handle.normalized(),
                meta.display_name or "",
                meta.description or "",
                meta.extra.get("participants", "") if meta.extra else "",
                acc.risk_score.value,
                "; ".join(acc.reasons),
                acc.created_at.value.isoformat() if acc.created_at else "",
                acc.last_seen.value.isoformat() if acc.last_seen else ""
            ])
    print(f"CSV report written to {csv_path}")

async def export_flagged_to_pdf(pdf_path="flagged_accounts_report.pdf"):
    if not PDF_AVAILABLE:
        print("FPDF is not installed. Run 'pip install fpdf' to enable PDF export.")
        return
    repo = SqlAccountRepository()
    flagged = await repo.list_flagged(limit=1000)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Flagged Telegram Accounts Report", ln=True, align='C')
    pdf.ln(5)
    for acc in flagged:
        meta = acc.metadata
        pdf.multi_cell(0, 8, txt=f"ID: {acc.id}\nPlatform: {meta.platform}\nHandle: {meta.handle.normalized()}\nDisplay Name: {meta.display_name or ''}\nDescription: {meta.description or ''}\nParticipants: {meta.extra.get('participants', '') if meta.extra else ''}\nRisk Score: {acc.risk_score.value}\nReasons: {'; '.join(acc.reasons)}\nFirst Seen: {acc.created_at.value.isoformat() if acc.created_at else ''}\nLast Seen: {acc.last_seen.value.isoformat() if acc.last_seen else ''}\n{'-'*60}")
    pdf.output(pdf_path)
    print(f"PDF report written to {pdf_path}")

if __name__ == "__main__":
    asyncio.run(export_flagged_to_csv())
    if PDF_AVAILABLE:
        asyncio.run(export_flagged_to_pdf())
