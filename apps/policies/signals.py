# apps/policies/signals.py
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from apps.notifications.models import NotificationLog, CHANNEL_SLACK, STATUS_QUEUED
from .models import MaintenancePolicy


def slack_mention_for_user(user) -> str:
    """
    Returns a real Slack mention if we have a Slack user ID (Uxxxx),
    otherwise falls back to a readable name (won't ping).
    """
    if not user:
        return ""
    slack_id = getattr(getattr(user, "profile", None), "slack_user_id", None)
    if slack_id:
        return f"<@{slack_id}>"
    return user.get_full_name() or getattr(user, "username", "") or ""


@receiver(post_save, sender=MaintenancePolicy)
def notify_policy_created(sender, instance: MaintenancePolicy, created, **kwargs):
    # Only on first create (not every edit)
    if not created:
        return

    def create_notification():
        owner = instance.owner  # <-- your model field
        mention = slack_mention_for_user(owner)
        mention_prefix = f"{mention} " if mention else ""

        # Pick a channel. If you're using incoming webhook fixed to one channel,
        # set SLACK_DEFAULT_CHANNEL="#maintenance-scheduler" in env and keep this.
        slack_to = (getattr(instance, "slack_channel", "") or os.getenv("SLACK_DEFAULT_CHANNEL", "")).strip()

        NotificationLog.objects.create(
            channel=CHANNEL_SLACK,              # "slack"
            to=slack_to,                        # "#maintenance-scheduler" (recommended) or whatever your adapter expects
            subject=f"New maintenance policy created: {instance.name}",
            message=(
                f"{mention_prefix}A new maintenance policy was created.\n"
                f"*Policy:* {instance.name}\n"
                f"*Type:* {instance.get_type_display() if hasattr(instance, 'get_type_display') else instance.type}\n"
                f"*Interval (days):* {instance.interval_days or '—'}"
            ),
            status=STATUS_QUEUED,
            maintenance_policy=instance,         # ✅ links it so your Slack blocks can render policy details
            payload={
                "policy_id": instance.pk,
                "policy_name": instance.name,
                "interval_days": instance.interval_days,
                "published": instance.published,
            },
        )

    transaction.on_commit(create_notification)
