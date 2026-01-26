# apps/policies/models.py
from django.db import models
from django.conf import settings


from django.contrib.auth.models import Group

from apps.fleet.models import Site, Robot, Payload
from apps.checklists.models import ChecklistTemplate

class MaintenanceRecord(models.Model):
    policy = models.ForeignKey(
        "policies.MaintenancePolicy",
        on_delete=models.CASCADE,
        related_name="records",
    )

    # Optional but useful:
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_maintenance_records",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    file = models.FileField(upload_to="maintenance_records/%Y/%m/%d/")
    notes = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Record for Policy #{self.policy_id} ({self.uploaded_at:%Y-%m-%d})"


class MaintenancePolicy(models.Model):
    """
    Defines when and how maintenance should be generated for matching robots.
    """
    TYPE_CHOICES = (
        ("time", "Time"),
        ("usage", "Usage"),
        ("condition", "Condition"),
    )

    name = models.CharField(max_length=120)

    # Optional JSON scope (keep if you use it)
    scope = models.JSONField(default=dict, blank=True)

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="policies",
    )

    published = models.BooleanField(default=False)

    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="time")
    interval_days = models.IntegerField(null=True, blank=True)
    window_days = models.IntegerField(null=True, blank=True)
    counter = models.CharField(max_length=60, blank=True)
    interval_units = models.IntegerField(null=True, blank=True)
    threshold = models.JSONField(null=True, blank=True)

    priority = models.CharField(max_length=4, default="P2")
    checklist_id = models.CharField(max_length=120, blank=True)
    docs_url = models.CharField(max_length=255, blank=True)


    checklist_template = models.ForeignKey(
        ChecklistTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="policies",
        help_text="Checklist template associated with this policy.",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_maintenance_policies",
        help_text="Primary person responsible for this policy.",
    )

    # ✅ NEW: which group is responsible
    owner_group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maintenance_policies",
        help_text="Group that owns this policy (e.g. Site Managers).",
    )

    # ✅ already added earlier:
    robots = models.ManyToManyField(
        Robot,
        blank=True,
        related_name="maintenance_policies",
        help_text="Robots this policy applies to.",
    )
    payloads = models.ManyToManyField(
        Payload,
        blank=True,
        related_name="maintenance_policies",
        help_text="Payloads this policy applies to.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ NEW: reminder state
    next_reminder_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_reminded_at = models.DateTimeField(null=True, blank=True)

    def compute_next_reminder(self):
        if self.type != "time" or not self.interval_days:
            return None
        base = self.last_reminded_at or timezone.now()
        return base + timedelta(days=self.interval_days)


    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name
