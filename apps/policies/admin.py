from django.contrib import admin
from .models import MaintenancePolicy


@admin.register(MaintenancePolicy)
class MaintenancePolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "priority", "interval_days", "window_days", "updated_at")
    list_filter = ("type", "priority")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basics", {"fields": ("name", "type", "priority")}),
        ("Scope", {"fields": ("scope",)}),
        ("Time-based", {"fields": ("interval_days", "window_days")}),
        ("Usage-based", {"fields": ("counter", "interval_units")}),
        ("Condition-based", {"fields": ("threshold",)}),
        ("Docs & Checklist", {"fields": ("checklist_id", "docs_url")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
