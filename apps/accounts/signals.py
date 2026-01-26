from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile
from django.contrib.auth import get_user_model


print("🔥 accounts.signals loaded")
User  = get_user_model()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
