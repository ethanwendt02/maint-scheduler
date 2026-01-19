from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MaintenanceRecordUploadForm
from .models import MaintenancePolicy, MaintenanceRecord
from .pdf import generate_policy_pdf


@login_required
def upload_maintenance_record(request, pk: int):
    policy = get_object_or_404(MaintenancePolicy, pk=pk)

    if request.method == "POST":
        form = MaintenanceRecordUploadForm(request.POST, request.FILES)
        if form.is_valid():
            rec: MaintenanceRecord = form.save(commit=False)
            rec.policy = policy
            rec.uploaded_by = request.user
            rec.save()

            # If you don't have a policy_detail page yet, use a safe redirect:
            return redirect("/portal/")
    else:
        form = MaintenanceRecordUploadForm()

    return render(request, "policies/upload_pdf.html", {"policy": policy, "form": form})


def policy_pdf(request, pk: int):
    policy = get_object_or_404(MaintenancePolicy, pk=pk)
    pdf_bytes = generate_policy_pdf(policy)

    if hasattr(pdf_bytes, "getvalue"):
        pdf_bytes = pdf_bytes.getvalue()

    filename = f"maintenance_policy_{policy.pk}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
