from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import ChecklistTemplate, ChecklistRun
from .serializers import ChecklistTemplateSerializer, ChecklistRunSerializer
from apps.workorders.models import WorkOrder
from apps.fleet.models import Robot

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django import forms
from .models import ChecklistRun


class ChecklistTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for checklist templates.
    """
    queryset = ChecklistTemplate.objects.all()
    serializer_class = ChecklistTemplateSerializer
    permission_classes = [IsAuthenticated]


class ChecklistRunViewSet(viewsets.ModelViewSet):
    """
    API for submitting completed checklists tied to work orders.
    """
    queryset = ChecklistRun.objects.all().select_related("work_order", "template", "signed_by")
    serializer_class = ChecklistRunSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="dashboard-metrics")
    def dashboard_metrics(self, request):
        total_deployed = Robot.objects.filter(status="active").count()

        robots_cleaned = (
            ChecklistRun.objects
            .filter(work_order__robot_id__isnull=False)
            .values("work_order__robot_id")
            .distinct()
            .count()
        )

    robots_needing_cleaning = max(total_deployed - robots_cleaned, 0)

    return Response({
        "counts": {
            "total_deployed": total_deployed,
            "robots_cleaned": robots_cleaned,
            "robots_needing_cleaning": robots_needing_cleaning,
        }
    })

class UploadChecklistForm(forms.ModelForm):
    class Meta:
        model = ChecklistRun
        fields = ("completed_pdf", )

@login_required
def upload_completed_pdf(request, run_id):
    run = get_object_or_404(ChecklistRun, pk=run_id)
    if request.method == "POST":
        form = UploadChecklistForm(request.POST, request.FILES, instance=run)
        if form.is_valid():
            form.save()
            return redirect("success-page")
    else:
        form = UploadChecklistForm(instance=run)
    return render(request, "upload_pdf.html", {"form": form})
