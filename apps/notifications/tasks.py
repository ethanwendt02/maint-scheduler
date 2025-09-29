from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.workorders.models import WorkOrder
from .utils import send_slack, send_email
from .slack_blocks import wo_blocks

REMINDER_DAYS = (14, 3)

@shared_task
def send_due_reminders():
    now = timezone.now()
    for wo in WorkOrder.objects.filter(status__in=["planned", "assigned"]):
        days_to_due = (wo.due_by.date() - now.date()).days
        if days_to_due in REMINDER_DAYS:
            text = f"Reminder: WO#{wo.id} for {wo.robot} at {wo.site} due {wo.due_by:%Y-%m-%d}."
            blocks = wo_blocks(wo)

            # Force to #maintenance-scheduler (what you asked for).
            # If your webhook doesn't allow overrides, remove `channel=` and keep the text label in footer.
            send_slack("#maintenance-scheduler", text=text, blocks=blocks)

            if wo.assigned_to and wo.assigned_to.email:
                send_email([wo.assigned_to.email], "Maintenance Reminder", text)

        if days_to_due == 0:
            send_slack("#maintenance-scheduler", text=f"Today due: WO#{wo.id}", blocks=wo_blocks(wo))

