from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.workorders.models import WorkOrder
from .utils import send_slack, send_email

REMINDER_DAYS = (14, 3)  # T-14 and T-3; add day-of in code


@shared_task
def send_due_reminders():
    """
    Send reminders for planned/assigned WorkOrders at T-14, T-3, and T-0 09:00.
    """
    now = timezone.now()
    for wo in WorkOrder.objects.filter(status__in=["planned", "assigned"]).select_related("site", "assigned_to"):
        days_to_due = (wo.due_by.date() - now.date()).days

        if days_to_due in REMINDER_DAYS:
            msg = f"Reminder: WO#{wo.id} for {wo.robot} at {wo.site} due {wo.due_by:%Y-%m-%d}."
            send_slack(wo.site.slack_channel or "#ops", msg)
            if wo.assigned_to and wo.assigned_to.email:
                send_email([wo.assigned_to.email], "Maintenance Reminder", msg)

        if days_to_due == 0 and now.hour == 9:
            msg = f"Today due: WO#{wo.id} — {wo.robot} at {wo.site}"
            send_slack(wo.site.slack_channel or "#ops", msg)
