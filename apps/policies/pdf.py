# apps/policies/pdf.py
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Flowable,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics


class Checkbox(Flowable):
    """Vector checkbox (prevents font square issues)."""
    def __init__(self, size=10):
        super().__init__()
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        c = self.canv
        s = self.size
        c.rect(0, 0, s, s)
        

def generate_policy_pdf(policy) -> bytes:
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    Title = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=10,
    )

    SectionHeader = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )

    Body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
    )

    elements = []

    # ===== HEADER =====
    elements.append(Paragraph(f"Maintenance Policy: {policy.name}", Title))
    elements.append(Spacer(1, 6))

    meta_data = [
        ["Site:", getattr(policy.site, "name", "—")],
        ["Priority:", getattr(policy, "priority", "—")],
        ["Type:", getattr(policy, "type", "—")],
    ]

    meta_table = Table(meta_data, colWidths=[1.2 * inch, 4.8 * inch])
    meta_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    elements.append(meta_table)
    elements.append(Spacer(1, 12))

    # ===== CHECKLIST =====
    elements.append(Paragraph("Checklist", SectionHeader))

    tmpl = getattr(policy, "checklist_template", None)

    if not tmpl:
        elements.append(Paragraph("No checklist template attached.", Body))
    else:
        items_qs = getattr(tmpl, "items", None)
        items = items_qs.all().order_by("section", "order", "id") if items_qs else []

        last_section = None

        for it in items:
            section = getattr(it, "section", "") or "General"
            text = (getattr(it, "text", "") or "").strip()

            if not text:
                continue

            if section != last_section:
                elements.append(Spacer(1, 8))
                elements.append(Paragraph(section, styles["Heading3"]))
                elements.append(Spacer(1, 4))
                last_section = section

            row = [
                Checkbox(10),
                Paragraph(text, Body),
                Paragraph('<font color="#999999">__________________________</font>', Body),
            ]

            t = Table([row], colWidths=[0.3 * inch, 4.5 * inch, 1.9 * inch])
            t.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )

            elements.append(t)

    # ===== SIGNATURE BLOCK =====
    elements.append(Spacer(1, 18))
    elements.append(Paragraph("Completion / Verification", SectionHeader))

    signature_data = [
        ["Completed by (name):", "______________________________", "Date:", "____________"],
        ["Signature:", "______________________________", "Time:", "____________"],
        ["Verified by (manager):", "______________________________", "", ""],
        ["Signature:", "______________________________", "", ""],
    ]

    signature_table = Table(
        signature_data,
        colWidths=[1.5 * inch, 2.7 * inch, 0.7 * inch, 1.5 * inch],
    )

    signature_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    elements.append(signature_table)

    doc.build(elements)
    return buf.getvalue()