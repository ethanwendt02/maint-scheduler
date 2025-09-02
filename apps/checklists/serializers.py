from rest_framework import serializers
from .models import ChecklistTemplate, ChecklistRun


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistTemplate
        fields = "__all__"


class ChecklistRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistRun
        fields = "__all__"
