from django.db import models


class Site(models.Model):
    """
    Represents a deployment site or home base.
    """
    name = models.CharField(max_length=120)
    tz = models.CharField(max_length=64, default="UTC")
    address = models.TextField(blank=True)
    flags = models.JSONField(blank=True, default=list)  # e.g., {"dusty": True}
    slack_channel = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return self.name


class Robot(models.Model):
    """
    Represents an individual robot unit.
    """
    model = models.CharField(max_length=60)      # e.g. "Falcon28"
    serial = models.CharField(max_length=60, unique=True)
    site = models.ForeignKey(Site, on_delete=models.PROTECT, null=True, blank=True)
    tier = models.CharField(max_length=4, default="P2")  # e.g., P0/P1/P2
    environments = models.JSONField(blank=True, null=True, default=list)        # e.g., {"dusty": True}
    status = models.CharField(max_length=32, default="active")  # active, in_maintenance, retired
    last_maintained = models.DateField(null=True, blank=True)  # NEW

    def __str__(self) -> str:
        return f"{self.model}#{self.serial}"
