from django.contrib import admin

from .models import ChecklistTemplate, ChecklistItem, ChecklistRun


class ChecklistItemInline(admin.TabularInline):
    """
    Inline editor for the individual checklist steps.
    These are the rows you see under a Checklist Template.
    """
    model = ChecklistItem
    extra = 0
    fields = ("order", "section", "text", "required", "kit_items")
    ordering = ("order", "id")
    show_change_link = True


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    """
    Admin for templates. **Important**: this only uses fields
    that actually exist now: name, description, created_at, updated_at.
    """
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description")
    ordering = ("name",)

    # Only show the real fields that exist on the model
    fieldsets = (
        (None, {
            "fields": ("name", "description"),
        }),
    )

    inlines = [ChecklistItemInline]


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    """
    Admin for actual checklist runs. Again: only use the current fields.
    """
    list_display = ("id", "template", "started_at", "completed_at", "created_by", "signed_by", "completed_pdf")
    fields = ("template", "started_at", "completed_pdf")
    list_filter = ("template", "started_at", "completed_at")
    search_fields = ("template__name",)
    raw_id_fields = ("template", "created_by", "signed_by")
    ordering = ("-started_at",)
