# apps/checklists/admin.py
from django.contrib import admin
from .models import ChecklistTemplate, ChecklistItem, ChecklistRun


class ChecklistItemInline(admin.TabularInline):
    """
    Inline editor for the NEW ChecklistItem rows (section, order, text).
    """
    model = ChecklistItem
    extra = 0
    fields = ("section", "order", "text")
    ordering = ("section", "order", "id")
    show_change_link = False


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    """
    Template now has just: name, description, created_at, updated_at.
    Items are edited via the inline above.
    """
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Checklist Template", {"fields": ("name", "description")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    inlines = [ChecklistItemInline]


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    """
    Simple view so you can inspect runs (optional).
    """
    list_display = ("id", "template", "started_at", "completed_at", "created_by", "signed_by")
    list_filter = ("template", "created_by", "signed_by")
    search_fields = ("template__name",)
    ordering = ("-started_at",)
    readonly_fields = ("started_at", "completed_at")
