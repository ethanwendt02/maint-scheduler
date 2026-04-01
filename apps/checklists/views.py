from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.fleet.models import Robot
from .models import ChecklistRun
from .serializers import ChecklistRunSerializer


class ChecklistRunViewSet(viewsets.ModelViewSet):
    queryset = ChecklistRun.objects.all().select_related(
        "work_order",
        "template",
        "signed_by",
    )
    serializer_class = ChecklistRunSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="dashboard-metrics")
    def dashboard_metrics(self, request):
        total_deployed = Robot.objects.filter(status="active").count()

        robots_cleaned = (
            ChecklistRun.objects
            .filter(work_order__robot_id__isnull=False)
            .values("work_order__robot_id")
            .distinct()
            .count()
        )

        robots_needing_cleaning = max(total_deployed - robots_cleaned, 0)

        return Response({
            "counts": {
                "total_deployed": total_deployed,
                "robots_cleaned": robots_cleaned,
                "robots_needing_cleaning": robots_needing_cleaning,
            }
        })