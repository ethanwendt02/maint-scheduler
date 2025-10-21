# apps/workorders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import WorkOrder
from apps.checklists.models import ChecklistRunItem

class ChecklistRunItemInline(admin.TabularInline):
    model = ChecklistRunItem
    extra = 0
    fields = ("order", "text", "kit_items", "done", "notes", "completed_by", "completed_at")
    readonly_fields = ("order", "text", "kit_items",)
    classes = ("collapse",)  # remove this line if you want it expanded by default

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "policy", "robot", "status", "checklist_progress")
    list_filter = ("status", "policy")
    search_fields = ("id", "robot__serial", "policy__name")
    inlines = (ChecklistRunItemInline,)

    def checklist_progress(self, obj):
        run = getattr(obj, "checklist_run", None)
        if not run:
            return "-"
        return run.progress

