# apps/checklists/admin.py
from django.contrib import admin
from django import forms

from .models import ChecklistTemplate, ChecklistItem  # adjust if names differ


def _existing_fields(model, candidates):
    """
    Return only the field names that actually exist on the model.
    Avoids admin system check errors if optional fields aren't present.
    """
    model_fields = {f.name for f in model._meta.get_fields()}
    return tuple(f for f in candidates if f in model_fields)


# ----- Forms (optional, keeps defaults) ---------------------------------------
class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = "__all__"
        help_texts = {
            "name": "Template name shown in Policies and Work Orders.",
            # These help_texts will be ignored if the fields don't exist:
            "description": "Optional: appears at the top of the run.",
            "section": "Optional: logical grouping/category.",
        }


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = _existing_fields(ChecklistItem, ("order", "text", "is_kit_item"))
    # If none of those exist, fall back to whatever the model has
    if not fields:
        fields = ("id",)  # keeps admin happy; you can tweak later
        readonly_fields = ("id",)


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    form = ChecklistTemplateForm

    list_display = _existing_fields(ChecklistTemplate, ("name", "section")) or ("name",)
    search_fields = ("name",)
    ordering = ("name",)

    inlines = [ChecklistItemInline]

    def get_fieldsets(self, request, obj=None):
        """
        Always return a fieldset dict that *contains* 'fields'.
        Only include fields that actually exist on the model.
        """
        M = ChecklistTemplate
        basics = _existing_fields(M, ("name", "description", "section"))
        if not basics:
            basics = ("name",)

        return (
            ("Checklist Template", {"fields": basics}),
        )
