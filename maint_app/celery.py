import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maint_app.settings")
app = Celery("maint_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "policy-reminders-daily": {
        "task": "apps.policies.tasks.send_due_policy_reminders",
        "schedule": 60 * 60 * 24,  # daily
    },
}
app.conf.beat_schedule = {
    "due-maintenance-check": {
        "task": "apps.policies.tasks.run_due_maintenance_notifications",
        "schedule": crontab(minute=0, hour=9),  # every day at 9am
    },
}