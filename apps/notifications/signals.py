from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import NotificationLog
from .tasks import send_notification_task

@receiver(post_save, sender=NotificationLog)
def send_on_queue(sender, instance: NotificationLog, created, **kwargs):
    if not created or instance.status != "queued":
        return

    def enqueue():
        try:
            send_notification_task.delay(instance.pk)
        except Exception as exc:
            # Don't 500 the admin page; record the failure instead
            NotificationLog.objects.filter(pk=instance.pk).update(
                status="failed",
                error=f"enqueue failed: {exc}",
            )

    transaction.on_commit(enqueue)
