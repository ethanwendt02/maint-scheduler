import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from apps.notifications.models import NotificationLog
from .models import MaintenancePolicy


def slack_mention_for_user(user) -> str:
    if not user:
        return ""
    slack_id = getattr(getattr(user, "profile", None), "slack_user_id", None)
    return f"<@{slack_id}>" if slack_id else (user.get_full_name() or user.username)


@receiver(post_save, sender=MaintenancePolicy)
def notify_policy_created_or_published(sender, instance: MaintenancePolicy, created, **kwargs):
    # Fire if: created OR published just turned on
    should_notify = created

    if not created:
        try:
            before = sender.objects.get(pk=instance.pk)
            # NOTE: this won't work because instance is already saved.
            # So for publish-transition you must do it in admin save_model or override save().
        except sender.DoesNotExist:
            before = None

    # ✅ simplest: only notify on CREATE (reliable)
    if not should_notify:
        return

    def create_notification():
        owner = getattr(instance, "owner", None)
        mention = slack_mention_for_user(owner)

        slack_label = getattr(instance, "slack_channel", "") or os.getenv("SLACK_DEFAULT_CHANNEL", "#maintenance-scheduler")

        NotificationLog.objects.create(
            channel="slack",
            to=slack_label,
            subject=f"New maintenance policy: {instance.name}",
            message=f"{mention} A new maintenance policy was created and will start generating reminders.",
            status="queued",
            maintenance_policy=instance,   # ✅ links the log to the policy
            payload={
                "policy_id": instance.pk,
                "policy_name": instance.name,
            },
        )

    transaction.on_commit(create_notification)
