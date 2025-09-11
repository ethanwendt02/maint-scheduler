from django.db import models
from django.contrib.auth import get_user_model
from apps.workorders.models import WorkOrder

User = get_user_model()


class ChecklistTemplate(models.Model):
    """
    A reusable checklist definition, e.g. "Falcon28 Cleaning v1".
    """

    checklist_id = models.CharField(max_length=120, unique=True)  # e.g., "clean-fans-v1"
    name = models.CharField(max_length=120)
    version = models.CharField(max_length=20, default="v1")

    # Items is a list of fields with structure like:
    # [{ "id": "open_payload", "label": "Open payload", "required": true, "type": "checkbox" }]
    items = models.JSONField(default=list, blank=True)
    kit   = models.JSONField(default=list, blank=True)
    requires_photos = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.version})"


class ChecklistRun(models.Model):
    """
    A completed checklist tied to a specific WorkOrder.
    """

    template   = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT)
    work_order = models.ForeignKey('workorders.WorkOrder', on_delete=models.PROTECT, null=True, blank=True)
    responses  = models.JSONField(default=dict, blank=True)      # item -> True/False
    tools_used = models.JSONField(default=list, blank=True)      # NEW: list of tools ticked
    photos     = models.JSONField(default=list, blank=True)
    notes      = models.TextField(blank=True)
    signed_by  = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"ChecklistRun for WO#{self.work_order.id}"
