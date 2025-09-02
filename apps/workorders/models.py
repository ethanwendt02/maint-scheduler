from django.db import models
from django.contrib.auth import get_user_model
from apps.fleet.models import Robot, Site
from apps.policies.models import MaintenancePolicy

User = get_user_model()


class WorkOrder(models.Model):
    """
    A scheduled or corrective maintenance job for a robot.
    """

    TYPE_CHOICES = (
        ("PM", "Preventive Maintenance"),
        ("CM", "Corrective Maintenance"),
        ("INSPECTION", "Inspection"),
    )

    STATUS_CHOICES = (
        ("planned", "Planned"),
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    robot = models.ForeignKey(Robot, on_delete=models.PROTECT)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    policy = models.ForeignKey(
        MaintenancePolicy, on_delete=models.SET_NULL, null=True, blank=True
    )

    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="PM")
    priority = models.CharField(max_length=4, default="P2")

    due_by = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="planned")

    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_workorders"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="completed_workorders"
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"WO#{self.id} - {self.robot} due {self.due_by:%Y-%m-%d}"

