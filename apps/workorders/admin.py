from django.contrib import admin
from .models import WorkOrder


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Work Orders.
    """

    list_display = (
        "id",
        "robot",
        "site",
        "type",
        "priority",
        "due_by",
        "status",
        "assigned_to",
        "completed_at",
    )

    list_filter = (
        "status",
        "priority",
        "type",
        "site",
    )

    search_fields = (
        "id",
        "robot__model",
        "robot__serial",
        "assigned_to__username",
        "completed_by__username",
    )

    ordering = ("-due_by",)
    date_hierarchy = "due_by"
