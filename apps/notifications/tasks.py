# apps/notifications/tasks.py
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import NotificationLog
from .utils import send_slack  # your adapter


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 5})
def send_notification_task(self, notification_id: int):
    # 1) Lock + claim
    with transaction.atomic():
        instance = NotificationLog.objects.select_for_update().get(pk=notification_id)

        if instance.status != "queued":
            return
        if instance.channel != "Slack":
            return

        instance.status = "sending"
        instance.error = ""
        instance.save(update_fields=["status", "error"])

    # 2) Build message
    channel = (instance.to or "").strip() or None
    text = instance.subject or "(no subject)"
    if instance.message:
        text = f"*{text}*\n{instance.message}"

    payload = instance.payload or {}
    if payload.get("checklist"):
        items = payload["checklist"]
        bulleted = "\n".join([f"• {i}" for i in items])
        text += f"\n\n*Checklist:*\n{bulleted}"

    filepaths = payload.get("files") or []

    # ✅ 3) EXTRA BULLETPROOFING GOES RIGHT HERE
    try:
        resp = send_slack(
            channel=channel,
            text=text,
            blocks=None,
            files=filepaths,
            initial_comment="Attachments",
        )
    except Exception as exc:
        instance.status = "failed"
        instance.error = str(exc)
        instance.save(update_fields=["status", "error"])
        raise  # IMPORTANT: re-raise so Celery retries

    # 4) Mark sent
    instance.status = "sent"
    instance.sent_at = timezone.now()
    instance.error = ""
    instance.save(update_fields=["status", "sent_at", "error"])
    return resp
