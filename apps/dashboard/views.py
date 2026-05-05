from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.shortcuts import render
from django.utils import timezone

from apps.fleet.models import Robot
from apps.policies.models import MaintenanceRecord


@staff_member_required
def metrics_dashboard(request):
    now = timezone.now()

    COMPLETED_LOOKBACK_DAYS = 30
    WEEKLY_LOOKBACK_WEEKS = 12
    TOP_N_POLICIES = 20

    completed_since = now - timedelta(days=COMPLETED_LOOKBACK_DAYS)
    weekly_since = now - timedelta(weeks=WEEKLY_LOOKBACK_WEEKS)

    total_deployed = Robot.objects.filter(status="active").count()

    robots_cleaned = (
        MaintenanceRecord.objects
        .filter(work_order__robot_id__isnull=False)
        .values("work_order__robot_id")
        .distinct()
        .count()
    )

    robots_needing_cleaning = max(total_deployed - robots_cleaned, 0)

    weekly_qs = (
        MaintenanceRecord.objects
        .filter(uploaded_at__gte=weekly_since)
        .annotate(week=TruncWeek("uploaded_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )

    weekly_labels = [
        row["week"].date().isoformat() if row["week"] else "unknown"
        for row in weekly_qs
    ]
    weekly_counts = [row["count"] for row in weekly_qs]

    top_policies_qs = (
        MaintenanceRecord.objects
        .filter(uploaded_at__gte=completed_since)
        .values("policy__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:TOP_N_POLICIES]
    )

    top_policy_labels = [row["policy__name"] or "Unnamed Policy" for row in top_policies_qs]
    top_policy_counts = [row["count"] for row in top_policies_qs]

    context = {
        "kpi": {
            "robots_cleaned": robots_cleaned,
            "robots_needing_cleaning": robots_needing_cleaning,
            "total_deployed": total_deployed,
        },
        "weekly_labels": weekly_labels,
        "weekly_counts": weekly_counts,
        "top_policy_labels": top_policy_labels,
        "top_policy_counts": top_policy_counts,
        "completed_lookback_days": COMPLETED_LOOKBACK_DAYS,
        "weekly_lookback_weeks": WEEKLY_LOOKBACK_WEEKS,
        "top_n": TOP_N_POLICIES,
    }

    return render(request, "dashboard/metrics.html", context)