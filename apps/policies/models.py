# apps/policies/models.py
from django.db import models
from apps.fleet.models import Site   # ← add this import

class MaintenancePolicy(models.Model):
    """
    Defines when and how maintenance should be generated for matching robots.
    Scope is a small JSON like: {"model": "Falcon28", "site": "Excyte"}.
    """
    TYPE_CHOICES = (
        ("time", "Time"),
        ("usage", "Usage"),
        ("condition", "Condition"),
    )

    name = models.CharField(max_length=120)

    # EXISTING: scope stores loose filters; keep it if you want
    scope = models.JSONField(default=dict, blank=True)

    # NEW: first-class relationship + publish switch
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, related_name="policies")
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
