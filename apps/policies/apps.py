# apps/policies/apps.py
from django.apps import AppConfig

class PoliciesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.policies"

    def ready(self):
        from . import signals  # noqa
