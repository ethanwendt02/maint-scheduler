from rest_framework import serializers
from .models import WorkOrder


class WorkOrderSerializer(serializers.ModelSerializer):
    robot_model = serializers.CharField(source="robot.model", read_only=True)
    robot_serial = serializers.CharField(source="robot.serial", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)

    class Meta:
        model = WorkOrder
        fields = "__all__"
