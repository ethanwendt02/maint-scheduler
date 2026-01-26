# apps/policies/signals.py
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from apps.notifications.models import NotificationLog
from apps.notifications.tasks import send_notification_task
from .models import MaintenancePolicy


def slack_mention_for_user(user) -> str:
    """
    Best: store Slack ID on user.profile.slack_user_id (e.g. U123ABC456)
    Mention format must be <@SLACK_ID>
    """
    if not user:
        return ""
    slack_id = getattr(getattr(user, "profile", None), "slack_user_id", None)
    if slack_id:
        return f"<@{slack_id}>"
    # fallback: no ping, just a name
    return user.get_full_name() or getattr(user, "username", "") or ""


@receiver(post_save, sender=MaintenancePolicy)
def notify_policy_created(sender, instance: MaintenancePolicy, created: bool, **kwargs):
    if not created:
        return

    # OPTIONAL: only notify when published
    # if not getattr(instance, "published", False):
    #     return

    def _after_commit():
        manager = getattr(instance, "manager", None)
        mention = slack_mention_for_user(manager)

        channel = (getattr(instance, "slack_channel", None) or os.getenv("SLACK_DEFAULT_CHANNEL") or "").strip()
        if not channel:
            channel = "#maintenance-scheduler"  # safe fallback

        base_url = (os.getenv("BASE_URL") or "").rstrip("/")
        admin_url = f"{base_url}/admin/policies/maintenancepolicy/{instance.pk}/change/" if base_url else ""

        subject = f"New maintenance policy created: {instance.name}"

        # Put the “real info” in message so it never shows blank
        frequency_days = getattr(instance, "frequency_days", None)
        next_due = getattr(instance, "next_due_date", None)

        message_lines = [
            f"{mention} A new maintenance policy was created.",
            f"*Policy:* {instance.name}",
        ]
        if frequency_days is not None:
            message_lines.append(f"*Frequency:* every {frequency_days} days")
        if next_due:
            message_lines.append(f"*Next Due:* {next_due}")
        if admin_url:
            message_lines.append(f"*Admin:* {admin_url}")

        nl = NotificationLog.objects.create(
            channel="Slack",
            to=channel,
            subject=subject,
            message="\n".join(message_lines),
            status="queued",
            payload={
                "policy_name": instance.name,
                "frequency_days": frequency_days,
                "due_date": str(next_due or ""),
                "url": admin_url,
            },
        )

        # ✅ enqueue AFTER commit so you don’t get 500s / partial saves
        send_notification_task.delay(nl.pk)

    transaction.on_commit(_after_commit)
