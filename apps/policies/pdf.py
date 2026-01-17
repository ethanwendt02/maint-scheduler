from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_policy_pdf(policy):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 750, f"Maintenance Policy: {policy.name}")

    # Basics
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Site: {policy.site.name if policy.site else 'N/A'}")
    c.drawString(50, 700, f"Owner: {policy.owner.get_full_name() if policy.owner else 'N/A'}")
    c.drawString(50, 680, f"Group: {policy.owner_group.name if policy.owner_group else 'N/A'}")
    c.drawString(50, 660, f"Priority: {policy.priority}")
    c.drawString(50, 640, f"Type: {policy.type}")

    c.drawString(50, 610, "Checklist Steps:")
    y = 590

    # Checklist items
    if policy.checklist_template:
        for item in policy.checklist_template.items.all():
            if y < 50:  # New page
                c.showPage()
                y = 750
            c.drawString(70, y, f"- {item.section}: {item.text}")
            y -= 20
    else:
        c.drawString(70, y, "No checklist template attached.")

    # Final signature block
    c.showPage()
    c.drawString(50, 750, "Technician Signature: ________________________")
    c.drawString(50, 720, "Manager Verification: _________________________")
    c.drawString(50, 690, "Date Completed: ______________________________")

    c.save()
    buffer.seek(0)
    return buffer
