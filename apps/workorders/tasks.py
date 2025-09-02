from celery import shared_task
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from apps.fleet.models import Robot
from apps.policies.models import MaintenancePolicy
from .models import WorkOrder


def robot_matches_scope(robot: Robot, scope: dict) -> bool:
    model_ok = scope.get("model") in (None, "*", robot.model)
    site_ok = scope.get("site") in (None, "*", (robot.site.name if robot.site else None))
    return model_ok and site_ok


@shared_task
def generate_work_orders():
    """
    Daily: for each time-based policy, ensure an upcoming WorkOrder exists.
    """
    now = timezone.now()

    for pol in MaintenancePolicy.objects.all():
        if pol.type != "time" or not pol.interval_days:
            continue

        for robot in Robot.objects.select_related("site").all():
            if not robot_matches_scope(robot, pol.scope or {}):
                continue

            # Skip if one already scheduled within the window
            window_start = now - relativedelta(days=pol.window_days or 0)
            exists = WorkOrder.objects.filter(
                robot=robot, policy=pol, status__in=["planned", "assigned"]
            ).filter(due_by__gte=window_start).exists()
            if exists:
                continue

            WorkOrder.objects.create(
                robot=robot,
                site=robot.site,
                policy=pol,
                type="PM",
                priority=pol.priority or "P2",
                due_by=now + relativedelta(days=+pol.interval_days),
            )
