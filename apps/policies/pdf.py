# apps/policies/pdf.py
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_policy_pdf(policy) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, f"Maintenance Policy: {policy.name}")
    y -= 28

    c.setFont("Helvetica", 11)
    c.drawString(72, y, f"Site: {getattr(policy.site, 'name', '') or '—'}")
    y -= 16
    c.drawString(72, y, f"Priority: {getattr(policy, 'priority', '') or '—'}")
    y -= 16
    c.drawString(72, y, f"Type: {getattr(policy, 'type', '') or '—'}")
    y -= 22

    # Checklist steps
    tmpl = getattr(policy, "checklist_template", None)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Checklist Steps")
    y -= 18

    c.setFont("Helvetica", 10)
    if not tmpl:
        c.drawString(72, y, "No checklist template attached.")
        y -= 14
    else:
        items_qs = getattr(tmpl, "items", None)
        items = items_qs.all().order_by("section", "order", "id") if items_qs else []

        last_section = None
        for it in items:
            section = getattr(it, "section", "") or ""
            if section != last_section:
                y -= 8
                c.setFont("Helvetica-Bold", 10)
                c.drawString(72, y, section or "General")
                y -= 14
                c.setFont("Helvetica", 10)
                last_section = section

            text = (getattr(it, "text", "") or "").strip()
            if not text:
                continue

            # wrap crudely (simple, reliable)
            max_chars = 95
            lines = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            for line in lines:
                if y < 72:
                    c.showPage()
                    y = height - 72
                    c.setFont("Helvetica", 10)
                c.drawString(90, y, f"- {line}")
                y -= 12

    # Signature block
    y -= 18
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Completion / Verification")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(72, y, "Completed by (name): ________________________________")
    y -= 18
    c.drawString(72, y, "Signature: ________________________________   Date: ____________")
    y -= 18
    c.drawString(72, y, "Verified by (manager): ________________________________")
    y -= 18
    c.drawString(72, y, "Signature: ________________________________   Time: ____________")

    c.showPage()
    c.save()
    return buf.getvalue()
