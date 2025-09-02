from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Site, Robot
from .serializers import SiteSerializer, RobotSerializer


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all().order_by("name")
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # remove "flags" from here:
    filterset_fields = ["tz"]                 # ← was ["tz", "flags"]
    search_fields = ["name", "slack_channel"]
    ordering_fields = ["name", "tz"]


class RobotViewSet(viewsets.ModelViewSet):
    """
    CRUD for robots.
    """
    queryset = Robot.objects.select_related("site").all().order_by("model", "serial")
    serializer_class = RobotSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["site", "model", "tier", "status"]   # exact filters
    search_fields = ["model", "serial", "site__name"]        # free-text search
    ordering_fields = ["model", "serial", "tier", "status"]

