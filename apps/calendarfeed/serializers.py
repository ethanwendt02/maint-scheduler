from rest_framework import serializers
from apps.workorders.models import WorkOrder


class WorkOrderCalendarSerializer(serializers.ModelSerializer):
    robot_model = serializers.CharField(source="robot.model", read_only=True)
    robot_serial = serializers.CharField(source="robot.serial", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)
    assigned_email = serializers.EmailField(source="assigned_to.email", read_only=True, allow_null=True)
    completed_by_email = serializers.EmailField(source="completed_by.email", read_only=True, allow_null=True)

    class Meta:
        model = WorkOrder
        fields = [
            "id",
            "type",
            "priority",
            "status",
            "due_by",
            "site",
            "site_name",
            "robot",
            "robot_model",
            "robot_serial",
            "policy",
            "assigned_to",
            "assigned_email",
            "completed_at",
            "completed_by",
            "completed_by_email",
            "notes",
        ]
