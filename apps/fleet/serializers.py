from rest_framework import serializers
from .models import Site, Robot


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = "__all__"


class RobotSerializer(serializers.ModelSerializer):
    # Handy read-only fields for UI convenience
    site_name = serializers.CharField(source="site.name", read_only=True)

    class Meta:
        model = Robot
        fields = "__all__"  # includes: model, serial, site, tier, environment, status, etc.
