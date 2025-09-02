from rest_framework import viewsets
from .models import MaintenancePolicy
from .serializers import MaintenancePolicySerializer

class MaintenancePolicyViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePolicy.objects.all()
    serializer_class = MaintenancePolicySerializer
