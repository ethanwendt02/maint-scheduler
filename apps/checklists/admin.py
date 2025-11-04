# apps/checklists/admin.py
from django.contrib import admin
from django import forms
from django.db import transaction
from .models import ChecklistTemplate, ChecklistItem

# ---- Forms --------------------------------------------------------------

class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ("order", "section", "text")
        widgets = {
            "text": forms.Textarea(attrs={"rows": 2}),
            "section": forms.TextInput(attrs={"placeholder": "Optional group header"}),
        }

    def clean_text(self):
        txt = (self.cleaned_data.get("text") or "").strip()
        if not txt:
            raise forms.ValidationError("Item text cannot be empty.")
        return txt

class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = ("name", "description")

# ---- Inlines ------------------------------------------------------------

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    form = ChecklistItemForm
    extra = 1
    fields = ("order", "section", "text")
    ordering = ("order", "id")
    show_change_link = False
    can_delete = True

# ---- Admin --------------------------------------------------------------

@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    form = ChecklistTemplateForm
    inlines = [ChecklistItemInline]

    list_display = ("name", "item_count", "created_at", "updated_at")
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Checklist Template", {"fields": ("name", "description")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    save_as = True  # handy: "Save as new"

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"

    @transaction.atomic
    def save_formset(self, request, form, formset, change):
        """
        Ensure every inline has a sane order, and belongs to this template.
        """
        instances = formset.save(commit=False)

        # attach template + normalize order
        # if order is blank/0, push it to the end
        max_order = (
            form.instance.items.aggregate(m=admin.models.Max("order"))["m"] or 0
        )

        for inst in instances:
            inst.template = form.instance
            if not inst.order or inst.order < 0:
                max_order += 1
                inst.order = max_order
            inst.save()

        # handle deletions
        for obj in formset.deleted_objects:
            obj.delete()

        # do not call formset.save() again – we saved manually

