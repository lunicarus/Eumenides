import asyncio
import csv
from datetime import datetime
import json

from app.infra.sql_repository import SqlAccountRepository
from app.domain.entities import FlaggedAccount
from app.domain.value_objects import Timestamp

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def human_date(dt, pt_format=False):
    if not dt:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    return dt.strftime("%d/%m/%Y %H:%M:%S") if pt_format else dt.strftime("%Y-%m-%d %H:%M:%S")


# English → Portuguese reason translations
REASON_PT_MAP = {
    "account name suggests seller activity (e.g. selling illegal content)": "nome de usuário sugere atividade de venda (ex: venda de conteúdo ilegal)",
    "display name suggests seller activity (e.g. selling illegal content)": "nome de exibição sugere atividade de venda (ex: venda de conteúdo ilegal)",
    "account name suggests suspicious/illicit content": "nome de usuário sugere conteúdo suspeito/ilícito",
    "display name suggests suspicious/illicit content": "nome de exibição sugere conteúdo suspeito/ilícito",
    "account name matches public Telegram handle pattern (potential risk)": "nome de usuário corresponde ao padrão público do Telegram (risco potencial)",
}


def translate_reason_pt(reason: str) -> str:
    return REASON_PT_MAP.get(reason, reason)


def safe_field(val):
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return "N/A"
    return str(val)


def safe_pdf_text(val):
    """For PDF: replace non-latin-1 chars with '?'."""
    if val is None:
        return "N/A"
    s = str(val)
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return s.encode("latin-1", errors="replace").decode("latin-1")


# ---------------- CSV EXPORTS ---------------- #

async def export_flagged_to_csv(csv_path="flagged_accounts_report.csv"):
    repo = SqlAccountRepository()
    flagged = await repo.list_flagged(limit=1000)
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(csv_path, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([f"Flagged Telegram Accounts Report - Generated: {report_date}"])
        writer.writerow([
            "ID", "Platform", "Handle", "Display Name", "Description",
            "Participants", "Risk Score", "Reasons", "First Seen", "Last Seen"
        ])

        for acc in flagged:
            meta = acc.metadata
            writer.writerow([
                safe_field(acc.id),
                safe_field(meta.platform),
                safe_field(meta.handle.normalized()),
                safe_field(meta.display_name),
                safe_field(meta.description),
                safe_field(meta.extra.get("participants", "") if meta.extra else "N/A"),
                safe_field(acc.risk_score.value),
                "; ".join(acc.reasons) if acc.reasons else "N/A",
                human_date(acc.created_at.value if acc.created_at else None),
                human_date(acc.last_seen.value if acc.last_seen else None),
            ])

    print(f"CSV report written to {csv_path}")


async def export_flagged_to_csv_pt(csv_path="relatorio_contas_suspeitas.csv"):
    repo = SqlAccountRepository()
    flagged = await repo.list_flagged(limit=1000)
    report_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    with open(csv_path, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)

        # header + explanation
        writer.writerow([f"Relatório de Contas Suspeitas do Telegram - Gerado em: {report_date}"])
        writer.writerow([
            "Este relatório lista contas públicas do Telegram identificadas como suspeitas por critérios automáticos. "
            "Cada linha representa uma conta analisada. Um score de risco próximo de 1 indica alta suspeita; próximo de 0 indica baixa suspeita. "
            "Veja a explicação de cada campo abaixo:"
        ])
        writer.writerow([
            "ID: identificador interno",
            "Plataforma: sempre 'telegram'",
            "Usuário: username público ou identificador",
            "Nome de Exibição: nome visível no perfil",
            "Descrição: texto do perfil",
            "Participantes: número de membros (se aplicável)",
            "Score de Risco (0-1)",
            "Score de Risco Bruto",
            "Motivos: razões para flag",
            "Primeira Vez Visto",
            "Última Vez Visto",
        ])

        for acc in flagged:
            meta = acc.metadata
            reasons_pt = "\n".join(f"- {translate_reason_pt(r)}" for r in acc.reasons) if acc.reasons else "N/A"
            raw_score = getattr(acc, "_raw_risk_score", acc.risk_score.value)

            writer.writerow([
                safe_field(acc.id),
                safe_field(meta.platform),
                safe_field(meta.handle.normalized()),
                safe_field(meta.display_name),
                safe_field(meta.description),
                safe_field(meta.extra.get("participants", "") if meta.extra else "N/A"),
                safe_field(acc.risk_score.value),
                safe_field(round(raw_score, 2)),
                reasons_pt,
                human_date(acc.created_at.value if acc.created_at else None, pt_format=True),
                human_date(acc.last_seen.value if acc.last_seen else None, pt_format=True),
            ])

    print(f"Relatório em português salvo em {csv_path}")


# ---------------- PDF EXPORTS ---------------- #

async def export_flagged_to_pdf(pdf_path="flagged_accounts_report.pdf"):
    if not PDF_AVAILABLE:
        print("FPDF is not installed. Run 'pip install fpdf' to enable PDF export.")
        return

    repo = SqlAccountRepository()
    flagged = await repo.list_flagged(limit=1000)
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 12, txt="Flagged Telegram Accounts Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, txt=f"Generated: {report_date}", ln=True, align='C')
    pdf.ln(4)

    for acc in flagged:
        meta = acc.metadata
        pdf.set_font("Arial", style="B", size=10)
        pdf.cell(0, 8, txt=f"Handle: {safe_pdf_text(meta.handle.normalized())}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, txt=f"Platform: {safe_pdf_text(meta.platform)}", ln=True)
        pdf.cell(0, 8, txt=f"Display Name: {safe_pdf_text(meta.display_name)}", ln=True)
        pdf.cell(0, 8, txt=f"Description: {safe_pdf_text(meta.description)}", ln=True)
        pdf.cell(0, 8, txt=f"Participants: {safe_pdf_text(meta.extra.get('participants', '') if meta.extra else 'N/A')}", ln=True)
        pdf.cell(0, 8, txt=f"Risk Score: {safe_pdf_text(acc.risk_score.value)}", ln=True)
        pdf.cell(0, 8, txt=f"Reasons: {safe_pdf_text('; '.join(acc.reasons) if acc.reasons else 'N/A')}", ln=True)
        pdf.cell(0, 8, txt=f"First Seen: {safe_pdf_text(human_date(acc.created_at.value if acc.created_at else None))}", ln=True)
        pdf.cell(0, 8, txt=f"Last Seen: {safe_pdf_text(human_date(acc.last_seen.value if acc.last_seen else None))}", ln=True)

        pdf.ln(2)
        pdf.set_draw_color(100, 100, 100)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

    pdf.output(pdf_path)
    print(f"PDF report written to {pdf_path}")


async def export_flagged_to_pdf_pt(pdf_path="relatorio_contas_suspeitas.pdf"):
    if not PDF_AVAILABLE:
        print("FPDF não está instalado. Rode 'pip install fpdf' para habilitar exportação PDF.")
        return

    repo = SqlAccountRepository()
    flagged = await repo.list_flagged(limit=1000)
    report_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 12, txt="Relatório de Contas Suspeitas do Telegram", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, txt=f"Gerado em: {report_date}", ln=True, align='C')
    pdf.ln(4)

    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 7, txt=(
        "Este relatório lista contas públicas do Telegram identificadas como suspeitas por critérios automáticos. "
        "Cada linha representa uma conta analisada. Um score de risco próximo de 1 indica alta suspeita; próximo de 0 indica baixa suspeita.\n\n"
        "ID: identificador interno\nPlataforma: sempre 'telegram'\nUsuário: username público ou identificador\n"
        "Nome de Exibição: nome visível no perfil\nDescrição: texto do perfil\nParticipantes: número de membros (se aplicável)\n"
        "Score de Risco: 0 a 1\nMotivos: razões para flag\nPrimeira Vez Visto: data/hora da primeira detecção\nÚltima Vez Visto: data/hora da última detecção"
    ), align='L')
    pdf.ln(2)

    for acc in flagged:
        meta = acc.metadata
        reasons_pt = "\n".join(f"- {translate_reason_pt(r)}" for r in acc.reasons) if acc.reasons else "N/A"

        pdf.set_font("Arial", style="B", size=10)
        pdf.cell(0, 8, txt=f"Usuário: {safe_pdf_text(meta.handle.normalized())}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, txt=f"Plataforma: {safe_pdf_text(meta.platform)}", ln=True)
        pdf.cell(0, 8, txt=f"Nome de Exibição: {safe_pdf_text(meta.display_name)}", ln=True)
        pdf.cell(0, 8, txt=f"Descrição: {safe_pdf_text(meta.description)}", ln=True)
        pdf.cell(0, 8, txt=f"Participantes: {safe_pdf_text(meta.extra.get('participants', '') if meta.extra else 'N/A')}", ln=True)
        pdf.cell(0, 8, txt=f"Score de Risco: {safe_pdf_text(acc.risk_score.value)}", ln=True)
        pdf.multi_cell(0, 8, txt=f"Motivos:\n{safe_pdf_text(reasons_pt)}")
        pdf.cell(0, 8, txt=f"Primeira Vez Visto: {safe_pdf_text(human_date(acc.created_at.value if acc.created_at else None, pt_format=True))}", ln=True)
        pdf.cell(0, 8, txt=f"Última Vez Visto: {safe_pdf_text(human_date(acc.last_seen.value if acc.last_seen else None, pt_format=True))}", ln=True)

        pdf.ln(2)
        pdf.set_draw_color(100, 100, 100)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

    pdf.output(pdf_path)
    print(f"Relatório PDF em português salvo em {pdf_path}")


# ---------------- MAIN ---------------- #

async def main():
    await export_flagged_to_csv()
    await export_flagged_to_csv_pt()
    if PDF_AVAILABLE:
        await export_flagged_to_pdf()
        await export_flagged_to_pdf_pt()


if __name__ == "__main__":
    asyncio.run(main())
