from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ClientProfile, Organization

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_client_profile(sender, instance, created, **kwargs):
    if not created:
        return
    # Choose how you pick an org. Option A: the first active org.
    org = Organization.objects.filter(is_active=True).first()
    # If you want to require explicit org assignment, you can skip creating
    # a profile when no org exists, but then handle that in the view (below).
    if org:
        ClientProfile.objects.get_or_create(user=instance, defaults={"organization": org})
