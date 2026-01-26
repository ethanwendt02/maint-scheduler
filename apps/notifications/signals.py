# apps/notifications/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import NotificationLog
from .tasks import send_notification_task

logger = logging.getLogger(__name__)

@receiver(post_save, sender=NotificationLog)
def send_on_queue(sender, instance: NotificationLog, created, **kwargs):
    if not created or instance.status != "queued":
        return

    def enqueue():
        try:
            send_notification_task.delay(instance.pk)
        except Exception:
            # Don't 500 the admin page
            logger.exception("Failed to enqueue notification %s", instance.pk)

    transaction.on_commit(enqueue)
