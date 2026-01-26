# apps/policies/signals.py
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import NotificationLog
from .models import MaintenancePolicy  # adjust import


def slack_mention_for_user(user) -> str:
    # Best: store Slack ID on the user/profile like user.profile.slack_user_id
    slack_id = getattr(getattr(user, "profile", None), "slack_user_id", None)
    return f"<@{slack_id}>" if slack_id else (user.get_full_name() or user.username)


@receiver(post_save, sender=MaintenancePolicy)
def notify_policy_created(sender, instance: MaintenancePolicy, created, **kwargs):
    if not created:
        return

    def create_notification():
        manager = getattr(instance, "manager", None)  # adjust if your field name differs
        mention = slack_mention_for_user(manager) if manager else ""

        NotificationLog.objects.create(
            channel="Slack",
            to=getattr(instance, "slack_channel", None) or os.getenv("SLACK_DEFAULT_CHANNEL", ""),
            subject=f"New maintenance policy created: {instance.name}",
            message=f"{mention} A new policy was created and will start scheduling reminders.",
            status="queued",
            payload={
                "policy_name": instance.name,
                "frequency_days": getattr(instance, "frequency_days", None),
                "due_date": str(getattr(instance, "next_due_date", "")),
                "url": f"{os.getenv('BASE_URL','').rstrip('/')}/admin/policies/maintenancepolicy/{instance.pk}/change/",
            },
        )

    transaction.on_commit(create_notification)
