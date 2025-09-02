from django.http import HttpResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from ics import Calendar, Event

from apps.workorders.models import WorkOrder
from .serializers import WorkOrderCalendarSerializer

# Simple token map for v1; replace with a DB model later.
VALID_TOKENS = {
    "demo-token": {"scope": "all"},
    # "site-excyte": {"site_name": "Excyte"},
    # "tech-alex": {"assigned_to_email": "alex@fieldai.com"},
}


def _filter_workorders_by_token(token: str):
    meta = VALID_TOKENS.get(token)
    if not meta:
        return None

    qs = WorkOrder.objects.select_related("robot", "site", "assigned_to", "completed_by", "policy")

    if meta.get("scope") == "all":
        return qs

    if "assigned_to_email" in meta:
        return qs.filter(assigned_to__email=meta["assigned_to_email"])

    if "site_name" in meta:
        return qs.filter(site__name=meta["site_name"])

    return qs


def ics_feed(request, token: str):
    qs = _filter_workorders_by_token(token)
    if qs is None:
        raise Http404("Invalid calendar token")

    cal = Calendar()
    for wo in qs:
        e = Event()
        e.name = f"{wo.robot.model}#{wo.robot.serial} — {wo.type}"
        e.begin = wo.due_by
        e.duration = {"hours": 1}
        lines = [
            f"Work Order: WO#{wo.id}",
            f"Site: {wo.site.name}",
            f"Status: {wo.status}",
            f"Priority: {wo.priority}",
            f"Assigned: {getattr(wo.assigned_to, 'email', 'Unassigned')}",
        ]
        if wo.policy:
            lines.append(f"Policy: {wo.policy.name}")
        if wo.completed_at:
            lines.append(f"Completed at: {wo.completed_at.isoformat()}")
        e.description = "\n".join(lines)
        cal.events.add(e)

    return HttpResponse(str(cal), content_type="text/calendar")


class UpcomingEventsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only JSON view of upcoming work orders.
    """
    serializer_class = WorkOrderCalendarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        token = self.request.query_params.get("token")
        qs = _filter_workorders_by_token(token) if token else None
        if qs is None:
            return WorkOrder.objects.none()
        now = timezone.now()
        return qs.filter(due_by__gte=now).order_by("due_by")

    @action(detail=False, methods=["get"])
    def all(self, request):
        """
        Optional: include past + future.
        GET /api/calendar/events/all/?token=...
        """
        token = request.query_params.get("token")
        qs = _filter_workorders_by_token(token)
        if qs is None:
            return Response([], status=status.HTTP_200_OK)
        data = self.get_serializer(qs.order_by("-due_by"), many=True).data
        return Response(data, status=status.HTTP_200_OK)
