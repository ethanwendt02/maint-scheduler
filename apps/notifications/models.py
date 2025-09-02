from django.db import models

class NotificationLog(models.Model):
    CHANNEL_CHOICES = [
        ("slack", "Slack"),
        ("email", "Email"),
    ]
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    to = models.CharField(max_length=255, blank=True, default="")      # email or slack channel
    subject = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True, default="")
    payload = models.JSONField(blank=True, null=True)                  # any extra context
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="queued")
    error = models.TextField(blank=True, default="")

    # Optional linkage to your domain objects
    work_order_id = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        tag = f"{self.channel}:{self.to or '-'}"
        return f"[{self.status}] {tag} — {self.subject or self.message[:40]}"
