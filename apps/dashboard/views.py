from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.shortcuts import render
from django.utils import timezone

from apps.policies.models import MaintenancePolicy
from apps.workorders.models import WorkOrder


@staff_member_required
def metrics_dashboard(request):
    now = timezone.now()

    # Tweak these without breaking anything
    OPEN_STATUSES = ["planned", "assigned", "in_progress"]
    DUE_SOON_DAYS = 7
    COMPLETED_LOOKBACK_DAYS = 30
    WEEKLY_LOOKBACK_WEEKS = 12
    TOP_N_POLICIES = 20

    due_soon_until = now + timedelta(days=DUE_SOON_DAYS)
    completed_since = now - timedelta(days=COMPLETED_LOOKBACK_DAYS)
    weekly_since = now - timedelta(weeks=WEEKLY_LOOKBACK_WEEKS)

    total_policies = MaintenancePolicy.objects.count()

    open_workorders = WorkOrder.objects.filter(status__in=OPEN_STATUSES)
    open_workorders_count = open_workorders.count()

    overdue_workorders_count = open_workorders.filter(due_by__lt=now).count()
    due_soon_workorders_count = open_workorders.filter(due_by__gte=now, due_by__lte=due_soon_until).count()

    # "Active policies" definition (scales + no schema changes):
    # policy that currently has at least one open work order
    active_policies_count = (
        MaintenancePolicy.objects.filter(workorder__status__in=OPEN_STATUSES)
        .distinct()
        .count()
    )

    completed_last_30d_count = WorkOrder.objects.filter(
        status="completed",
        completed_at__gte=completed_since,
        policy__isnull=False,
    ).count()

    # Weekly completions (last N weeks)
    weekly_qs = (
        WorkOrder.objects.filter(status="completed", completed_at__gte=weekly_since)
        .annotate(week=TruncWeek("completed_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )
    weekly_labels = [
        row["week"].date().isoformat() if row["week"] else "unknown"
        for row in weekly_qs
    ]
    weekly_counts = [row["count"] for row in weekly_qs]

    # Top N policies by completed cycles in last 30d
    top_policies_qs = (
        WorkOrder.objects.filter(
            status="completed",
            completed_at__gte=completed_since,
            policy__isnull=False,
        )
        .values("policy__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:TOP_N_POLICIES]
    )
    top_policy_labels = [row["policy__name"] for row in top_policies_qs]
    top_policy_counts = [row["count"] for row in top_policies_qs]

    context = {
        # KPI cards
        "kpi": {
            "active_policies": active_policies_count,
            "total_policies": total_policies,
            "open_workorders": open_workorders_count,
            "overdue_workorders": overdue_workorders_count,
            "due_soon_workorders": due_soon_workorders_count,
            "completed_last_30d": completed_last_30d_count,
        },
        # Charts
        "weekly_labels": weekly_labels,
        "weekly_counts": weekly_counts,
        "top_policy_labels": top_policy_labels,
        "top_policy_counts": top_policy_counts,
        # Display bits
        "due_soon_days": DUE_SOON_DAYS,
        "completed_lookback_days": COMPLETED_LOOKBACK_DAYS,
        "weekly_lookback_weeks": WEEKLY_LOOKBACK_WEEKS,
        "top_n": TOP_N_POLICIES,
    }

    return render(request, "dashboard/metrics.html", context)
