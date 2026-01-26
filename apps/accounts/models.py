from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    slack_user_id = models.CharField(
        max_length=32,
        blank=True,
        help_text="Slack user ID (e.g. U03ABCDEF)",
    )

    def __str__(self):
        return f"Profile for {self.user}"
