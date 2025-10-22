# apps/workorders/apps.py
from django.apps import AppConfig
import logging

log = logging.getLogger(__name__)


class WorkordersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workorders"
    verbose_name = "Work Orders"

    def ready(self):
        """
        Try to load signals, but don't break the app if optional checklist-run
        models aren't present (or are being refactored).
        """
        try:
            from . import signals  # noqa: F401
            log.debug("Workorders signals loaded.")
        except Exception as e:
            # Soft-disable signals if ChecklistRun/ChecklistRunItem aren't available
            log.warning("Workorders signals disabled: %s", e)
