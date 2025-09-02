from django.contrib import admin
from .models import ChecklistTemplate, ChecklistRun


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ("checklist_id", "name", "version", "requires_photos", "updated_at")
    list_filter = ("requires_photos", "version")
    search_fields = ("checklist_id", "name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("checklist_id",)


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    list_display = ("work_order", "template", "signed_by", "signed_at")
    list_filter = ("signed_at", "template")
    search_fields = ("work_order__id", "template__checklist_id", "signed_by__username")
    autocomplete_fields = ("work_order", "template", "signed_by")
    readonly_fields = ("created_at", "updated_at")
