# apps/checklists/admin.py
from django.contrib import admin
from django import forms
from .models import ChecklistTemplate, ChecklistItem


class ChecklistItemInlineForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ("order", "section", "text")
        help_texts = {
            "section": "Optional group heading (e.g., “Maintenance Kit”, “Pre-check”, “Procedure”). "
                       "Items with the same section will be shown together.",
            "order": "Integer order inside the template (lower appears first).",
        }


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    form = ChecklistItemInlineForm
    extra = 0
    fields = ("order", "section", "text")
    ordering = ("section", "order", "id")
    show_change_link = False


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "item_count")
    search_fields = ("name",)
    inlines = [ChecklistItemInline]
    fieldsets = (
        ("Basics", {"fields": ("name", "description")}),
        ("How grouping works",
         {"description":
              "Each item may have a <b>section</b> (group title). "
              "In the UI, items are shown grouped by section then by order."
          }),
    )

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"
