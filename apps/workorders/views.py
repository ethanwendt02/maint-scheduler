from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import WorkOrder
from .serializers import WorkOrderSerializer


class WorkOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing work orders.
    """
    queryset = WorkOrder.objects.all().select_related(
        "robot", "site", "assigned_to", "completed_by", "policy"
    )
    serializer_class = WorkOrderSerializer

    @action(detail=False, methods=["get"], url_path="maintenance-dashboard")
    def maintenance_dashboard(self, request):
        open_statuses = ["planned", "assigned", "in_progress"]

        pending_robot_rows = (
            WorkOrder.objects
            .filter(status__in=open_statuses)
            .values(
                "robot_id",
                "robot__model",
                "robot__serial",
                "robot__site__name",
            )
            .distinct()
            .order_by("robot__serial")
        )

        pending_robot_ids = [row["robot_id"] for row in pending_robot_rows]

        completed_robot_rows = (
            WorkOrder.objects
            .filter(status="completed")
            .exclude(robot_id__in=pending_robot_ids)
            .values(
                "robot_id",
                "robot__model",
                "robot__serial",
                "robot__site__name",
            )
            .distinct()
            .order_by("robot__serial")
        )

        robots_completed_maintenance = [
            {
                "id": row["robot_id"],
                "label": f'{row["robot__model"]}#{row["robot__serial"]}',
                "model": row["robot__model"],
                "serial": row["robot__serial"],
                "site_name": row["robot__site__name"],
            }
            for row in completed_robot_rows
        ]

        robots_yet_to_complete_maintenance = [
            {
                "id": row["robot_id"],
                "label": f'{row["robot__model"]}#{row["robot__serial"]}',
                "model": row["robot__model"],
                "serial": row["robot__serial"],
                "site_name": row["robot__site__name"],
            }
            for row in pending_robot_rows
        ]

        return Response({
            "counts": {
                "completed": len(robots_completed_maintenance),
                "pending": len(robots_yet_to_complete_maintenance),
            },
            "robots_completed_maintenance": robots_completed_maintenance,
            "robots_yet_to_complete_maintenance": robots_yet_to_complete_maintenance,
        })