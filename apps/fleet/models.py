# apps/fleet/models.py
from django.db import models
from django.conf import settings

class Site(models.Model):
    name = models.CharField(max_length=120, unique=True)
    tz = models.CharField(max_length=64, default="UTC")
    address = models.CharField(max_length=255, blank=True)
    flags = models.JSONField(default=dict, blank=True)
    slack_channel = models.CharField(max_length=120, blank=True)  # already used in admin

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Non-auth contact you can assign as a robot manager (created from Notion)."""
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return self.name if not self.email else f"{self.name} <{self.email}>"


class Payload(models.Model):
    """Payload attached to a robot (e.g., Lidar X2, Gripper v3)."""
    name = models.CharField(max_length=120, unique=True)
    type = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return self.name


class ClientGroup(models.Model):
    name = models.CharField(max_length=120)
    site = models.ForeignKey(
        "Site",
        on_delete=models.CASCADE,
        related_name="client_groups",   # matches your admin’s `obj.client_groups.count()`
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="client_groups",
    )

    def __str__(self):
        return f"{self.name} @ {self.site.name}"


class Robot(models.Model):
    model = models.CharField(max_length=60)
    serial = models.CharField(max_length=60, unique=True)
    site = models.ForeignKey(Site, on_delete=models.PROTECT, null=True, blank=True)
    tier = models.CharField(max_length=4, default="P2")
    status = models.CharField(max_length=32, default="active")

    # if you previously had `environment = JSONField(...)`, rename to plural for admin code:
    environments = models.JSONField(default=list, blank=True)  # list of strings like ["indoor","wet"]

    # NEW fields used by your admin / Notion sync:
    robot_type = models.CharField(max_length=60, blank=True)
    location = models.CharField(max_length=120, blank=True)   # within-site location
    licenses = models.JSONField(default=list, blank=True)      # list of license numbers
    payloads = models.ManyToManyField("Payload", blank=True)   # use string to avoid NameError
    manager = models.ForeignKey(
        "Contact", null=True, blank=True, on_delete=models.SET_NULL, related_name="robots"
    )

    def __str__(self):
        return f"{self.model}#{self.serial}"
