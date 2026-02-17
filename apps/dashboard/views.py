from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.shortcuts import render
from django.utils import timezone

from apps.policies.models import MaintenancePolicy, MaintenanceRecord


@staff_member_required
def metrics_dashboard(request):
    now = timezone.now()

    DUE_SOON_DAYS = 7
    COMPLETED_LOOKBACK_DAYS = 30
    WEEKLY_LOOKBACK_WEEKS = 12
    TOP_N_POLICIES = 20

    due_soon_until = now + timedelta(days=DUE_SOON_DAYS)
    completed_since = now - timedelta(days=COMPLETED_LOOKBACK_DAYS)
    weekly_since = now - timedelta(weeks=WEEKLY_LOOKBACK_WEEKS)

    # ✅ Policies
    total_policies = MaintenancePolicy.objects.count()
    active_policies = MaintenancePolicy.objects.filter(published=True).count()

    # ✅ Completed cycles = MaintenanceRecord uploads
    completed_last_30d = MaintenanceRecord.objects.filter(
        uploaded_at__gte=completed_since
    ).count()

    # ✅ Trend: records per week
    weekly_qs = (
        MaintenanceRecord.objects.filter(uploaded_at__gte=weekly_since)
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

    # ✅ Top policies by completed cycles (records) last 30d
    top_policies_qs = (
        MaintenanceRecord.objects.filter(uploaded_at__gte=completed_since)
        .values("policy__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:TOP_N_POLICIES]
    )
    top_policy_labels = [row["policy__name"] for row in top_policies_qs]
    top_policy_counts = [row["count"] for row in top_policies_qs]

    # ✅ Due soon / overdue policies using next_reminder_at
    due_policies = MaintenancePolicy.objects.filter(
        published=True,
        next_reminder_at__isnull=False,
    )
    overdue_policies = due_policies.filter(next_reminder_at__lt=now).count()
    due_soon_policies = due_policies.filter(
        next_reminder_at__gte=now,
        next_reminder_at__lte=due_soon_until
    ).count()

    context = {
        "kpi": {
            "active_policies": active_policies,
            "total_policies": total_policies,
            "completed_last_30d": completed_last_30d,
            "overdue_policies": overdue_policies,
            "due_soon_policies": due_soon_policies,
        },
        "weekly_labels": weekly_labels,
        "weekly_counts": weekly_counts,
        "top_policy_labels": top_policy_labels,
        "top_policy_counts": top_policy_counts,
        "due_soon_days": DUE_SOON_DAYS,
        "completed_lookback_days": COMPLETED_LOOKBACK_DAYS,
        "weekly_lookback_weeks": WEEKLY_LOOKBACK_WEEKS,
        "top_n": TOP_N_POLICIES,
    }

    return render(request, "dashboard/metrics.html", context)
