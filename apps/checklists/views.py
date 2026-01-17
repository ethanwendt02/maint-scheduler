from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import ChecklistTemplate, ChecklistRun
from .serializers import ChecklistTemplateSerializer, ChecklistRunSerializer
from apps.workorders.models import WorkOrder

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

    @action(detail=False, methods=["post"], url_path="submit")
    def submit_checklist(self, request):
        """
        Payload:
          - work_order (id)
          - checklist_id
          - responses (dict)
          - photos (list, optional)
          - notes (optional)
        """
        data = request.data
        try:
            work_order = WorkOrder.objects.get(id=data.get("work_order"))
        except WorkOrder.DoesNotExist:
            return Response({"error": "Invalid work_order id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = ChecklistTemplate.objects.get(checklist_id=data.get("checklist_id"))
        except ChecklistTemplate.DoesNotExist:
            return Response({"error": "Invalid checklist_id"}, status=status.HTTP_400_BAD_REQUEST)

        run, _ = ChecklistRun.objects.get_or_create(work_order=work_order, template=template)
        run.responses = data.get("responses", {})
        run.photos = data.get("photos", [])
        run.notes = data.get("notes", "")
        run.signed_by = request.user
        run.signed_at = timezone.now()
        run.save()

        work_order.status = "completed"
        work_order.completed_at = run.signed_at
        work_order.completed_by = request.user
        work_order.save(update_fields=["status", "completed_at", "completed_by"])

        return Response(ChecklistRunSerializer(run).data, status=status.HTTP_201_CREATED)

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

