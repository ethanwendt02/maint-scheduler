# apps/policies/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.notifications.models import NotificationLog
from .models import MaintenancePolicy

@receiver(post_save, sender=MaintenancePolicy)
def notify_policy_created(sender, instance: MaintenancePolicy, created, **kwargs):
    if not created:
        return

    # Send to the policy's site slack channel by default
    channel = instance.site.slack_channel or ""

    NotificationLog.objects.create(
        kind="policy_created",
        status="queued",
        channel="Slack",
        to=channel,
        subject=f"New Maintenance Policy: {instance.name}",
        maintenance_policy=instance,
    )
