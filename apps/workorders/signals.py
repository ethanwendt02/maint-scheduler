# apps/workorders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import WorkOrder

# Try to import optional run models; if missing, we just don't wire signals.
try:
    # In your codebase there is ChecklistItem (template item), not ChecklistRunItem.
    # If you really had a run-item model, import it; otherwise this will fail and we no-op.
    from apps.checklists.models import ChecklistRun  # type: ignore
except Exception:
    ChecklistRun = None  # type: ignore


def _runs_available() -> bool:
    return ChecklistRun is not None


@receiver(post_save, sender=WorkOrder)
def ensure_checklist_run(sender, instance: WorkOrder, created, **kwargs):
    """
    If you keep the ChecklistRun feature, you can re-enable this body later.
    For now, bail out cleanly if the runs system isn't present.
    """
    if not _runs_available():
        return

    # --- If you decide to keep runs, restore logic here, e.g.:
    # template = getattr(instance.policy, "checklist_template", None)
    # if not template:
    #     return
    # run, _ = ChecklistRun.objects.get_or_create(template=template)
    # instance.checklist_run = run
    # instance.save(update_fields=["checklist_run"])
