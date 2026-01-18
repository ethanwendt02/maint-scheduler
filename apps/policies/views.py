from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import MaintenancePolicy
from .pdf import generate_policy_pdf

def policy_pdf(request, pk: int):
    policy = get_object_or_404(MaintenancePolicy, pk=pk)
    pdf_bytes = generate_policy_pdf(policy)

    if hasattr(pdf_bytes, "getvalue"):
        pdf_bytes = pdf_bytes.getvalue()

    filename = f"maintenance_policy_{policy.pk}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response

