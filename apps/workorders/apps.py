# apps/workorders/apps.py
from django.apps import AppConfig


class WorkordersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workorders"
    verbose_name = "Work Orders"

    def ready(self):
        """
        This ensures that Django imports signals.py when the app loads,
        so automatic checklist run creation and other hooks are active.
        """
        from . import signals  # noqa
