# apps/checklists/admin.py
from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe

from .models import (
    ChecklistTemplate,
    ChecklistItem,
    ChecklistRun,
    ChecklistRunItem,
)

# helper: only include fields that exist on the model
def _existing_fields(model, candidates):
    model_fields = {f.name for f in model._meta.get_fields()}
    return tuple(f for f in candidates if f in model_fields)


# ---------------- Template + Items ----------------

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = _existing_fields(ChecklistItem, ("order", "text", "required", "kit_items"))
    ordering = ("order", "id")


class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = "__all__"  # don't list non-existent fields


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    form = ChecklistTemplateForm
    inlines = (ChecklistItemInline,)

    list_display = _existing_fields(ChecklistTemplate, ("name",)) or ("__str__",)
    search_fields = _existing_fields(ChecklistTemplate, ("name", "description")) or ("name",)

    # dynamic, safe fieldsets
    def get_fieldsets(self, request, obj=None):
        basics = _existing_fields(ChecklistTemplate, ("name", "description"))
        advanced = _existing_fields(ChecklistTemplate, (
            # put optional fields here if your model actually has them
            # e.g. "category", "tags"
        ))
        fieldsets = []
        if basics:
            fieldsets.append(("Template", {"fields": basics}))
        if advanced:
            fieldsets.append(("Advanced", {"fields": advanced}))
        return tuple(fieldsets) if fieldsets else None


# ---------------- Runs + Run Items ----------------

class ChecklistRunItemInline(admin.TabularInline):
    model = ChecklistRunItem
    extra = 0
    # show checkboxes & notes editable; keep source fields read-only
    readonly_fields = _existing_fields(ChecklistRunItem, ("order", "text", "kit_items"))
    fields = _existing_fields(ChecklistRunItem, (
        "order", "text", "kit_items", "done", "notes", "completed_by", "completed_at"
    ))
    ordering = ("order", "id")


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    inlines = (ChecklistRunItemInline,)

    list_display = _existing_fields(ChecklistRun, ("template", "created_at")) or ("template",)
    list_filter = _existing_fields(ChecklistRun, ("template",))
    search_fields = ("template__name",)

    readonly_fields = _existing_fields(ChecklistRun, ("created_at", "started_at", "finished_at", "created_by"))

    def get_fieldsets(self, request, obj=None):
        basics = _existing_fields(ChecklistRun, ("template", "created_by"))
        timing = _existing_fields(ChecklistRun, ("created_at", "started_at", "finished_at"))
        fieldsets = []
        if basics:
            fieldsets.append(("Run", {"fields": basics}))
        if timing:
            fieldsets.append(("Timestamps", {"fields": timing}))
        return tuple(fieldsets) if fieldsets else None


@admin.register(ChecklistRunItem)
class ChecklistRunItemAdmin(admin.ModelAdmin):
    list_display = _existing_fields(ChecklistRunItem, ("run", "order", "text", "done")) or ("run", "text", "done")
    list_filter = _existing_fields(ChecklistRunItem, ("done", "completed_by"))
    search_fields = ("text", "run__template__name")
    ordering = ("run", "order", "id")
