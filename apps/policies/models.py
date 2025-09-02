from django.db import models


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
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="time")

    # Narrow which robots this policy applies to (by model, site, tier, etc.)
    scope = models.JSONField(default=dict)

    # Time-based scheduling
    interval_days = models.IntegerField(null=True, blank=True)
    window_days = models.IntegerField(default=10)

    # Usage-based scheduling
    counter = models.CharField(max_length=32, blank=True)        # e.g., "hours"
    interval_units = models.IntegerField(null=True, blank=True)  # e.g., 500

    # Condition-based threshold (store simple rule data)
    threshold = models.JSONField(null=True, blank=True)          # e.g., {"temp_motor": {">": 85, "for": "5m"}}

    priority = models.CharField(max_length=4, default="P2")      # P0–P3, etc.
    checklist_id = models.CharField(max_length=120, blank=True)  # links to a ChecklistTemplate
    docs_url = models.CharField(max_length=255, blank=True)      # link to customer/internal procedure

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
