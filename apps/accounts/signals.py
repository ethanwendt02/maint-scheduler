from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Profile  # whatever your profile model is actually called

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    # Create only once, safely
    Profile.objects.get_or_create(user=instance)