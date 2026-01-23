# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import NotificationLog
from .tasks import send_notification_task

@receiver(post_save, sender=NotificationLog)
def send_on_queue(sender, instance: NotificationLog, created, **kwargs):
    if not created or instance.status != "queued":
        return

    # enqueue ONLY after transaction commits successfully
    transaction.on_commit(lambda: send_notification_task.delay(instance.pk))
