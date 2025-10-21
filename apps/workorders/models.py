# apps/workorders/models.py
from __future__ import annotations

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.fleet.models import Robot, Site
from apps.policies.models import MaintenancePolicy
from apps.checklists.models import ChecklistRun  # model exists per your project

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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workorders",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_workorders",
    )

    notes = models.TextField(blank=True)

    # ✅ New: each WorkOrder can have a concrete, checkable checklist instance
    checklist_run = models.OneToOneField(
        ChecklistRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workorder",
        help_text="Concrete instance of the template with checkable items.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-due_by", "-created_at")
        indexes = [
            models.Index(fields=("status", "due_by")),
            models.Index(fields=("policy",)),
            models.Index(fields=("robot",)),
            models.Index(fields=("site",)),
        ]

    def __str__(self) -> str:
        return f"WO#{self.id} - {self.robot} due {self.due_by:%Y-%m-%d}"

    # --------- Convenience / UX helpers ---------

    def clean(self):
        """
        If site wasn't set explicitly, default it from the robot to reduce form friction.
        """
        super().clean()
        if self.robot and not self.site_id:
            self.site = self.robot.site

    @property
    def checklist_progress(self) -> str:
        """
        Human-friendly progress like '3/10' for the attached checklist run.
        """
        run = self.checklist_run
        if not run:
            return "-"
        total = run.items.count()
        if not total:
            return "0/0"
        done = run.items.filter(done=True).count()
        return f"{done}/{total}"

    @transaction.atomic
    def ensure_checklist_run(self, created_by: User | None = None) -> ChecklistRun | None:
        """
        Create (once) a ChecklistRun + items from the policy's checklist_template.
        Safe to call multiple times; will no-op if one already exists or no template is attached.

        Returns the ChecklistRun instance, or None if no template.
        """
        if self.checklist_run_id:  # already present
            return self.checklist_run

        if not self.policy or not hasattr(self.policy, "checklist_template") or not self.policy.checklist_template:
            return None

        # Import inline to avoid circulars if your apps import each other at import time.
        from apps.checklists.models import ChecklistRun, ChecklistRunItem

        template = self.policy.checklist_template
        run = ChecklistRun.objects.create(
            template=template,
            created_at=timezone.now(),
            created_by=created_by,
        )

        # Copy template items into the run
        items_to_create = []
        for it in template.items.all():
            items_to_create.append(
                ChecklistRunItem(
                    run=run,
                    template_item=it,
                    order=it.order,
                    text=it.text,
                    kit_items=it.kit_items,
                )
            )
        if items_to_create:
            ChecklistRunItem.objects.bulk_create(items_to_create)

        # attach and persist
        self.checklist_run = run
        self.save(update_fields=["checklist_run", "updated_at"])
        return run

