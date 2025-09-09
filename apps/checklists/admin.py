from django.contrib import admin
from .models import ChecklistTemplate, ChecklistRun
from django import forms


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    form = ChecklistTemplateForm
    exclude = ("items",)  # hide the raw JSON/list field
    list_display = ("checklist_id", "name", "version", "requires_photos")
    search_fields = ("checklist_id", "name")


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    form = ChecklistRunForm
    exclude = ["responses", "photos"]


class ChecklistTemplateForm(forms.ModelForm):
    items_text = forms.CharField(
        required=False,
        help_text="Comma-separated checklist items (e.g., battery, sensors, locomotion)."
    )

    class Meta:
        model = ChecklistTemplate
        fields = ["checklist_id", "name", "version", "items_text", "requires_photos"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and isinstance(self.instance.items, list):
            self.fields["items_text"].initial = ", ".join(self.instance.items)

    def clean(self):
        cleaned = super().clean()
        text = cleaned.get("items_text", "")
        cleaned["items"] = [t.strip() for t in text.split(",") if t.strip()] if text else []
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.items = self.cleaned_data.get("items", [])
        if commit:
            obj.save()
        return obj


class ChecklistRunForm(forms.ModelForm):
    responses_text = forms.CharField(
        required=False,
        help_text="Key:Value pairs separated by commas (e.g., battery:ok, sensors:fail)."
    )
    photos_text = forms.CharField(
        required=False,
        help_text="Comma-separated photo filenames or IDs."
    )

    class Meta:
        model = ChecklistRun
        fields = ["work_order", "template", "responses_text", "photos_text", "notes", "signed_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.instance.responses, dict):
            self.fields["responses_text"].initial = ", ".join(f"{k}:{v}" for k, v in self.instance.responses.items())
        if isinstance(self.instance.photos, list):
            self.fields["photos_text"].initial = ", ".join(self.instance.photos)

    def clean(self):
        cleaned = super().clean()
        responses = {}
        text = cleaned.get("responses_text", "")
        for pair in text.split(","):
            if ":" in pair:
                k, v = pair.split(":", 1)
                responses[k.strip()] = v.strip()
        cleaned["responses"] = responses
        cleaned["photos"] = [p.strip() for p in cleaned.get("photos_text", "").split(",") if p.strip()]
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.responses = self.cleaned_data.get("responses", {})
        obj.photos = self.cleaned_data.get("photos", [])
        if commit:
            obj.save()
        return obj