from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import NotificationLog
from .slack import post_message, upload_files

@receiver(post_save, sender=NotificationLog)
def send_on_queue(sender, instance: NotificationLog, created, **kwargs):
    # Only act when newly created and queued for sending
    if not created or instance.status != "queued":
        return

    try:
        if instance.channel == "Slack":
            # Choose channel: prefer row's `to` if it looks like a channel ID; else fallback to env default
            channel = (instance.to or "").strip() or None

            # Build the message
            text = instance.subject or "(no subject)"
            if instance.message:
                text = f"*{text}*\n{instance.message}"

            # Optionally add structured blocks from payload
            blocks = None
            p = instance.payload or {}
            if p.get("checklist"):
                items = p["checklist"]
                bulleted = "\n".join([f"• {i}" for i in items])
                text += f"\n\n*Checklist:*\n{bulleted}"

            # Send the message
            resp = post_message(text=text, channel=channel)
            thread_ts = resp.get("ts")

            # Optional: upload any files the row references (absolute paths in payload["files"])
            filepaths = p.get("files") or []
            if filepaths:
                upload_files(filepaths=filepaths, channel=channel, initial_comment="Attachments", thread_ts=thread_ts)

            instance.status = "sent"
            instance.sent_at = timezone.now()
            instance.error = ""
            instance.save(update_fields=["status", "sent_at", "error"])

        else:
            # Not Slack → do nothing here (your email path handles Email channel)
            pass

    except Exception as exc:
        instance.status = "failed"
        instance.error = str(exc)
        instance.save(update_fields=["status", "error"])
