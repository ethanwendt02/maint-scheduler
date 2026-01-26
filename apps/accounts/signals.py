# apps/accounts/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile  # <-- MUST match your model name

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    # create for new users
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        # optional: ensure older users also have one when they get saved
        Profile.objects.get_or_create(user=instance)
