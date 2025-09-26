from django.db import models
from django.conf import settings

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

class ClientGroup(models.Model):
    """
    A client-visible group of users that belongs to a Site.
    Used by the client portal to resolve user -> site -> data.
    """
    name = models.CharField(max_length=120)
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="client_groups",
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="client_groups",
        blank=True,
    )

    class Meta:
        unique_together = (("site", "name"),)
        ordering = ("site__name", "name")

    def __str__(self) -> str:
        return f"{self.name} @ {self.site.name}"

