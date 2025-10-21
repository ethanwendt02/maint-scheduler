# apps/workorders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import WorkOrder

# We keep ChecklistRun editing in its own admin (with its own inline of items)
# to avoid the E202 error. From WorkOrder, we link to it and show progress.

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "policy", "robot", "status", "due_by", "checklist_progress", "checklist_link")
    list_filter = ("status", "policy", "site", "priority", "type")
    search_fields = ("id", "robot__serial", "policy__name", "site__name", "notes")
    ordering = ("-due_by", "-created_at")

    readonly_fields = ("checklist_progress", "_checklist_link_readonly")

    fieldsets = (
        ("Work order", {
            "fields": ("robot", "site", "policy", "type", "priority", "due_by", "status")
        }),
        ("Assignment & Completion", {
            "fields": ("assigned_to", "completed_at", "completed_by")
        }),
        ("Checklist", {
            "description": "Create or open the run to check off steps.",
            "fields": ("checklist_progress", "_checklist_link_readonly")
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj)

    # ---- pretty helpers

    def checklist_progress(self, obj: WorkOrder):
        return obj.checklist_progress
    checklist_progress.short_description = "Checklist"

    def checklist_link(self, obj: WorkOrder):
        """
        A small button in the changelist to open/create the run.
        """
        if not obj.pk:
            return "-"
        if obj.checklist_run_id:
            url = reverse("admin:checklists_checklistrun_change", args=[obj.checklist_run_id])
            return format_html('<a class="button" href="{}">Open checklist</a>', url)
        # no run yet; offer creation link to the change page where a user can save ↔ create via action
        url = reverse("admin:workorders_workorder_change", args=[obj.pk])
        return format_html('<a class="button" href="{}">Create on save</a>', url)
    checklist_link.short_description = "Checklist"

    def _checklist_link_readonly(self, obj: WorkOrder):
        """
        A readonly field on the form with open/create link.
        """
        if not obj or not obj.pk:
            return "Save this Work Order first."
        if obj.checklist_run_id:
            url = reverse("admin:checklists_checklistrun_change", args=[obj.checklist_run_id])
            return format_html('<a class="button" href="{}">Open checklist</a>', url)
        return format_html('<span>No checklist run yet.</span> '
                           '<span style="margin-left:8px;">(Save, then use the action below or re-open this page.)</span>')
    _checklist_link_readonly.short_description = "Checklist run"

    # ---- optional admin action to create the run from selected WOs

    actions = ["action_create_checklist_run"]

    def action_create_checklist_run(self, request, queryset):
        created = 0
        for wo in queryset:
            if wo.ensure_checklist_run(getattr(request, "user", None)):
                created += 1
        self.message_user(request, f"Created/ensured checklist runs for {created} work order(s).")
    action_create_checklist_run.short_description = "Create/ensure checklist run"

