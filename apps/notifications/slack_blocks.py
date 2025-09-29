from datetime import datetime
from typing import Optional

from django.utils import timezone

# --- helpers ---------------------------------------------------------------

def _dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    # render in local TZ if you prefer; timezone.localtime handles aware datetimes
    try:
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt.strftime("%Y-%m-%d %H:%M")

def _interval_str(policy) -> str:
    """
    Best-effort human string for the policy interval.
    Your MaintenancePolicy model (from the zip) contains fields like interval_type/units.
    Adjust this formatter if your exact field names differ.
    """
    # common patterns seen in the project:
    #  - policy.type in ("time", "usage", "condition")
    #  - policy.interval_days / interval_hours, or interval_units
    #  - policy.interval_value + policy.interval_units (e.g., 500 + "hours")
    parts = []
    # try a few likely attributes safely
    val = getattr(policy, "interval_value", None)
    units = getattr(policy, "interval_units", None)
    if val and units:
        parts.append(f"{val} {units}")
    else:
        days = getattr(policy, "interval_days", None)
        hours = getattr(policy, "interval_hours", None)
        if days:
            parts.append(f"{days} days")
        if hours:
            parts.append(f"{hours} hours")
    if not parts:
        t = getattr(policy, "type", None) or getattr(policy, "interval_type", None)
        if t:
            parts.append(str(t))
    return " / ".join(parts) if parts else "—"

# --- blocks ----------------------------------------------------------------

def wo_blocks(wo) -> list:
    """
    Build Slack Block Kit for a WorkOrder, including the fields you asked for:
    Next due, Status, Completed, Interval, Robot.
    """
    policy = getattr(wo, "policy", None)
    robot = getattr(wo, "robot", None)
    site = getattr(wo, "site", None)

    # Header/title
    title = getattr(wo, "title", None) or f"WO #{wo.id}"
    header = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{title}*"}
    }

    # First 2-column field set (left/right)
    fields_primary = {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*Checklist Run:*\n{getattr(wo, 'run_label', '—')}"},  # keep if you use it, else remove
            {"type": "mrkdwn", "text": f"*Status:*\n{getattr(wo, 'status', '—') or '—'}"},
            {"type": "mrkdwn", "text": f"*Robot:*\n{getattr(robot, 'model', '')} {getattr(robot, 'serial', '')}".strip() or "—"},
            {"type": "mrkdwn", "text": f"*Site:*\n{getattr(site, 'name', '—')}"},
            {"type": "mrkdwn", "text": f"*Started:*\n{_dt(getattr(wo, 'started_at', None))}"},
            {"type": "mrkdwn", "text": f"*Completed:*\n{_dt(getattr(wo, 'completed_at', None))}"},
        ],
    }

    divider = {"type": "divider"}

    # Second field set with Policy info
    fields_policy = {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*Template:*\n{getattr(policy, 'checklist_id', '—')}"},
            {"type": "mrkdwn", "text": f"*Version:*\n{getattr(policy, 'version', '—')}"},
            {"type": "mrkdwn", "text": f"*Policy:*\n{getattr(policy, 'name', '—')}"},
            {"type": "mrkdwn", "text": f"*Interval:*\n{_interval_str(policy) if policy else '—'}"},
            {"type": "mrkdwn", "text": f"*Next due:*\n{_dt(getattr(wo, 'due_by', None))}"},
            {"type": "mrkdwn", "text": f"*Scope:*\n{getattr(policy, 'scope', '—')}"},
        ],
    }

    # Footer (optional)
    context = {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "Posted from Maintenance Scheduler • #maintenance-scheduler"}
        ]
    }

    return [header, fields_primary, divider, fields_policy, divider, context]
