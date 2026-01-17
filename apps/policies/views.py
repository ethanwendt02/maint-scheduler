# apps/policies/views.py
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from .models import MaintenancePolicy
from .pdf import generate_policy_pdf

def _can_view_policy_pdf(user, policy: MaintenancePolicy) -> bool:
    # Superusers/admins can always download
    if user.is_superuser or user.is_staff:
        return True

    # Owner can download
    if getattr(policy, "owner_id", None) == user.id:
        return True

    # Anyone in the owner_group can download
    owner_group = getattr(policy, "owner_group", None)
    if owner_group and user.groups.filter(id=owner_group.id).exists():
        return True

    return False

@login_required
def maintenance_policy_pdf(request, pk: int):
    policy = get_object_or_404(MaintenancePolicy, pk=pk)

    if not _can_view_policy_pdf(request.user, policy):
        raise Http404()

    pdf_bytes = generate_policy_pdf(policy)

    filename = f"maintenance_policy_{policy.pk}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
