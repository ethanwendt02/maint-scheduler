from django.db import models
from django.utils import timezone
from typing import List
from .utils import send_slack, send_email   # uses the webhook+email helpers from step 2

# Canonical constants to avoid case mistakes
CHANNEL_SLACK = "slack"
CHANNEL_EMAIL = "email"

STATUS_QUEUED = "queued"
STATUS_SENT   = "sent"
STATUS_FAILED = "failed"

class NotificationLog(models.Model):
    CHANNEL_CHOICES = [
        (CHANNEL_SLACK, "Slack"),
        (CHANNEL_EMAIL, "Email"),
    ]
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    to = models.CharField(max_length=255, blank=True, default="")      # email OR a Slack label (e.g., "#ops")
    subject = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True, default="")
    payload = models.JSONField(blank=True, null=True)                  # any extra context
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    error = models.TextField(blank=True, default="")

    # Optional linkage to your domain objects
    work_order_id = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        tag = f"{self.channel}:{self.to or '-'}"
        preview = (self.subject or self.message or "")[:40]
        return f"[{self.status}] {tag} — {preview}"

    # ---------- helpers ----------
    def _as_text_for_slack(self) -> str:
        """Compose Slack-friendly text with bold subject on first line."""
        subj = (self.subject or "").strip()
        body = (self.message or "").strip()
        if subj and body:
            return f"*{subj}*\n{body}"
        return f"*{subj}*" if subj else body

    def _mark(self, status: str, error_msg: str = "") -> None:
        self.status = status
        self.error = error_msg
        if status == STATUS_SENT and not self.sent_at:
            self.sent_at = timezone.now()
        self.save(update_fields=["status", "error", "sent_at"])

    # ---------- main API ----------
    def send(self) -> bool:
        """
        Sends this notification according to `channel`.
        Returns True on success, False on failure.
        """
        try:
            if self.channel == CHANNEL_EMAIL:
                # Basic email path. Expand send_email as needed.
                recipients: List[str] = [e.strip() for e in (self.to or "").split(",") if e.strip()]
                send_email(recipients, self.subject or "(no subject)", self.message or "")
                self._mark(STATUS_SENT)
                return True

            if self.channel == CHANNEL_SLACK:
                # NOTE: with Incom
