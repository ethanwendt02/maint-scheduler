# apps/notifications/tasks.py
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import NotificationLog
from .utils import send_slack  # your adapter


def build_slack_blocks(instance: NotificationLog) -> list:
    """
    Build a Slack Block Kit message so content never shows up "blank".
    """
    subject = instance.subject or "(no subject)"
    body = instance.message or ""
    payload = instance.payload or {}

    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": subject[:150]}
    })

    # Body
    if body.strip():
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": body[:3000]}
        })

    # Optional checklist
    checklist = payload.get("checklist") or []
    if checklist:
        bullets = "\n".join([f"• {x}" for x in checklist])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Checklist:*\n{bullets[:3000]}"}
        })

    # Optional fields (policy metadata)
    fields = []
    if payload.get("policy_name"):
        fields.append({"type": "mrkdwn", "text": f"*Policy:*\n{payload['policy_name']}"})
    if payload.get("due_date"):
        fields.append({"type": "mrkdwn", "text": f"*Due:*\n{payload['due_date']}"})
    if payload.get("frequency_days"):
        fields.append({"type": "mrkdwn", "text": f"*Every:*\n{payload['frequency_days']} days"})

    if fields:
        blocks.append({"type": "section", "fields": fields})

    # Optional link button
    if payload.get("url"):
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Open in Maint Scheduler"},
                "url": payload["url"]
            }]
        })

    return blocks


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 5})
def send_notification_task(self, notification_id: int):
    # 1) Lock + claim
    with transaction.atomic():
        instance = NotificationLog.objects.select_for_update().get(pk=notification_id)

        if instance.status != "queued":
            return
        if instance.channel != "slack":
            return

        instance.status = "sending"
        instance.error = ""
        instance.save(update_fields=["status", "error"])

    channel = (instance.to or "").strip() or None
    blocks = build_slack_blocks(instance)
    filepaths = (instance.payload or {}).get("files") or []

    # 2) Send (and retry safely)
    try:
        resp = send_slack(
            channel=channel,
            text=instance.subject or "(no subject)",  # Slack uses this as fallback/notification preview
            blocks=blocks,
            files=filepaths,
            initial_comment="Attachments" if filepaths else None,
        )
    except Exception as exc:
        instance.status = "failed"
        instance.error = str(exc)
        instance.save(update_fields=["status", "error"])
        raise  # keep retries

    # 3) Mark sent
    instance.status = "sent"
    instance.sent_at = timezone.now()
    instance.error = ""
    instance.save(update_fields=["status", "sent_at", "error"])
    return resp

@shared_task
def send_queued_notifications(limit=50):
    qs = NotificationLog.objects.filter(status=STATUS_QUEUED).order_by("created_at")[:limit]
    for n in qs:
        n.send()
