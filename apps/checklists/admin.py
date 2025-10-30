# apps/checklists/admin.py
from django.contrib import admin
from django import forms

from .models import ChecklistTemplate, ChecklistItem  # keep it minimal/safe


def _existing_fields(model, candidates):
    """Return only the field names that truly exist on the model."""
    have = {f.name for f in model._meta.get_fields()}
    return tuple(f for f in candidates if f in have)


# ----- Inline for ChecklistItem ------------------------------------------------
class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    ordering = ("order",)

    # Only include columns that exist in your DB
    fields = _existing_fields(
        ChecklistItem,
        ("order", "text", "is_kit", "requires_photo"),
    ) or ("text",)
    readonly_fields = ()
    show_change_link = False


# ----- Form for ChecklistTemplate (optional help texts) ------------------------
class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = "__all__"
        help_texts = {
            "name": "Template name shown in Policies and Work Orders.",
            "description": "Optional: appears at the top of the run.",
        }


# ----- Admin for ChecklistTemplate --------------------------------------------
@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    form = ChecklistTemplateForm
    inlines = [ChecklistItemInline]

    # be conservative here: only the columns we’re confident exist
    list_display = _existing_fields(ChecklistTemplate, ("name",)) or ("__str__",)
    search_fields = _existing_fields(ChecklistTemplate, ("name",)) or ()
    ordering = ("name",)

    # IMPORTANT: every fieldset **must** contain a "fields" key
    def get_fieldsets(self, request, obj=None):
        basics = _existing_fields(ChecklistTemplate, ("name", "description"))
        # fall back to just the name if description is missing
        if not basics:
            basics = ("name",)
        return (
            ("Checklist Template", {"fields": basics}),
        )
