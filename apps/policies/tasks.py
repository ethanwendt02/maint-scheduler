# apps/policies/tasks.py
import os
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from apps.notifications.models import NotificationLog
from apps.notifications.tasks import send_notification_task
from .models import MaintenancePolicy


def slack_mention_for_user(user) -> str:
    if not user:
        return ""
    slack_id = getattr(getattr(user, "profile", None), "slack_user_id", None)
    return f"<@{slack_id}>" if slack_id else (user.get_full_name() or user.username)


@shared_task
def process_policy_reminders():
    now = timezone.now()

    qs = MaintenancePolicy.objects.filter(
        published=True,
        type="time",
        interval_days__isnull=False,
        next_reminder_at__isnull=False,
        next_reminder_at__lte=now,
    ).select_related("owner")

    for policy in qs:
        with transaction.atomic():
            policy = MaintenancePolicy.objects.select_for_update().get(pk=policy.pk)

            # re-check under lock
            if not policy.next_reminder_at or policy.next_reminder_at > timezone.now():
                continue

            mention = slack_mention_for_user(policy.owner)

            channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#maintenance-scheduler")
            base_url = os.getenv("BASE_URL", "").rstrip("/")
            admin_url = f"{base_url}/admin/policies/maintenancepolicy/{policy.pk}/change/" if base_url else ""

            nl = NotificationLog.objects.create(
                channel="Slack",
                to=channel,
                subject=f"Maintenance due: {policy.name}",
                message=f"{mention} Maintenance is due for *{policy.name}*.\n{admin_url}",
                status="queued",
                payload={
                    "policy_id": policy.pk,
                    "policy_name": policy.name,
                    "interval_days": policy.interval_days,
                    "admin_url": admin_url,
                },
            )

            send_notification_task.delay(nl.pk)

            policy.last_reminded_at = now
            policy.next_reminder_at = now + timedelta(days=int(policy.interval_days))
            policy.save(update_fields=["last_reminded_at", "next_reminder_at"])
