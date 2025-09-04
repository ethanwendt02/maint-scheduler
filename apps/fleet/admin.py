# apps/fleet/admin.py
from django.contrib import admin
from django import forms

from .models import Site, Robot

# ---------- Site (as you already had) ----------
class SiteAdminForm(forms.ModelForm):
    flags_text = forms.CharField(
        required=False,
        label="Flags",
        help_text="Comma-separated flags (e.g., priority, needs_badge, north).",
    )

    class Meta:
        model = Site
        fields = ["name", "tz", "address", "flags_text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.flags or []
        if isinstance(current, list):
            self.fields["flags_text"].initial = ", ".join(current)
        elif isinstance(current, dict):
            self.fields["flags_text"].initial = ", ".join(f"{k}:{v}" for k, v in current.items())

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("flags_text") or "").strip()
        cleaned["flags"] = [t.strip() for t in text.split(",") if t.strip()] if text else []
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.flags = self.cleaned_data.get("flags", [])
        if commit:
            obj.save()
        return obj


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    form = SiteAdminForm
    exclude = ["flags"]
    list_display = ("name", "tz")
    search_fields = ("name", "tz", "address")


# ---------- Robot (friendly environments) ----------
class RobotAdminForm(forms.ModelForm):
    environments_text = forms.CharField(
        required=False,
        label="Environments",
        help_text="Comma-separated environments (e.g., indoor, warehouse, wet).",
    )

    class Meta:
        model = Robot
        fields = ["model", "serial", "site", "tier", "status", "environments_text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.environments or []
        if isinstance(current, list):
            self.fields["environments_text"].initial = ", ".join(current)
        elif isinstance(current, dict):
            self.fields["environments_text"].initial = ", ".join(f"{k}:{v}" for k, v in current.items())

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("environments_text") or "").strip()
        cleaned["environments"] = [t.strip() for t in text.split(",") if t.strip()] if text else []
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.environments = self.cleaned_data.get("environments", [])
        if commit:
            obj.save()
        return obj


@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    form = RobotAdminForm
    exclude = ["environments"]  # hide the raw JSON field
    list_display = ("model", "serial", "site", "tier", "status")
    list_filter = ("site", "tier", "status", "model")
    search_fields = ("serial", "model", "site__name")
    autocomplete_fields = ("site",)
    ordering = ("model", "serial")

