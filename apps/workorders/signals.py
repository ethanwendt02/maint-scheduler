# apps/workorders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from apps.workorders.models import WorkOrder
from apps.checklists.models import ChecklistRun, ChecklistRunItem

@receiver(post_save, sender=WorkOrder)
def ensure_checklist_run(sender, instance: WorkOrder, created, **kwargs):
    """
    If the work order's policy has a checklist template, create a ChecklistRun
    with items copied from the template (only once).
    """
    policy = getattr(instance, "policy", None)
    if not policy:
        return

    template = getattr(policy, "checklist_template", None)
    if not template:
        return

    # already has a run? nothing to do
    if instance.checklist_run_id:
        return

    run = ChecklistRun.objects.create(template=template, created_at=timezone.now())
    items = []
    for it in template.items.all():
        items.append(ChecklistRunItem(
            run=run,
            template_item=it,
            order=it.order,
            text=it.text,
            kit_items=it.kit_items,
        ))
    if items:
        ChecklistRunItem.objects.bulk_create(items)

    instance.checklist_run = run
    instance.save(update_fields=["checklist_run"])
