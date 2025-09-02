from rest_framework import viewsets
from .models import WorkOrder
from .serializers import WorkOrderSerializer


class WorkOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing work orders.
    """
    queryset = WorkOrder.objects.all().select_related("robot", "site", "assigned_to", "completed_by", "policy")
    serializer_class = WorkOrderSerializer
