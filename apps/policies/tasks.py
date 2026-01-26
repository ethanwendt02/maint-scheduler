# apps/policies/tasks.py
import os
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from apps.notifications.models import NotificationLog
from .models import MaintenancePolicy  # adjust import


def slack_mention_for_user(user) -> str:
    slack_id = getattr(getattr(user, "profile", None), "slack_user_id", None)
    return f"<@{slack_id}>" if slack_id else (user.get_full_name() or user.username)


@shared_task
def send_due_policy_reminders():
    today = timezone.localdate()

    # You’ll need some “due” logic. Examples:
    # - instance.next_due_date exists
    # - OR compute from last_completed + frequency_days
    due_qs = MaintenancePolicy.objects.filter(active=True, next_due_date__lte=today)

    for policy in due_qs:
        manager = getattr(policy, "manager", None)
        mention = slack_mention_for_user(manager) if manager else ""

        NotificationLog.objects.create(
            channel="Slack",
            to=getattr(policy, "slack_channel", None) or os.getenv("SLACK_DEFAULT_CHANNEL", ""),
            subject=f"Maintenance due: {policy.name}",
            message=f"{mention} This maintenance is due now. Please complete it.",
            status="queued",
            payload={
                "policy_name": policy.name,
                "frequency_days": getattr(policy, "frequency_days", None),
                "due_date": str(getattr(policy, "next_due_date", "")),
                "url": f"{os.getenv('BASE_URL','').rstrip('/')}/admin/policies/maintenancepolicy/{policy.pk}/change/",
            },
        )

        # bump next due date forward so you don’t spam every run
        freq = getattr(policy, "frequency_days", None) or 7
        policy.next_due_date = (policy.next_due_date or today) + timedelta(days=int(freq))
        policy.save(update_fields=["next_due_date"])
