from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    slack_user_id = models.CharField(max_length=32, blank=True, default="")

    def __str__(self):
        return f"Profile: {self.user}"
