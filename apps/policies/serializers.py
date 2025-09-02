from rest_framework import serializers
from .models import MaintenancePolicy

class MaintenancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePolicy
        fields = "__all__"
