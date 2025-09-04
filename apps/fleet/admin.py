# apps/fleet/admin.py
from django.contrib import admin
from django import forms

from .models import Site, Robot   # ← import both models

# ---------- Site (friendly Flags) ----------

class SiteAdminForm(forms.ModelForm):
    # human-friendly text box instead of raw JSON
    flags_text = forms.CharField(
        required=False,
        label="Flags",
        help_text="Comma-separated flags (e.g., priority, needs_badge, north).",
    )

    class Meta:
        model = Site
        fields = ["name", "tz", "address", "flags_text"]  # ← do not expose 'flags' raw

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.flags or []
        if isinstance(current, list):
            self.fields["flags_text"].initial = ", ".join(current)
        elif isinstance(current, dict):
            # only if you ever switch flags to dict, show key:value pairs
            self.fields["flags_text"].initial = ", ".join(f"{k}:{v}" for k, v in current.items())

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("flags_text") or "").strip()
        if text:
            # "a, b, c" → ["a","b","c"]
            cleaned["flags"] = [t.strip() for t in text.split(",") if t.strip()]
        else:
            cleaned["flags"] = []
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.flags = self.cleaned_data.get("flags", [])
        if commit:
            obj.save()
        return obj

class RobotInline(admin.TabularInline):
    model = Robot
    extra = 0
    autocomplete_fields = ("site",)

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    form = SiteAdminForm
    exclude = ["flags"]  # hide raw JSON field
    list_display = ("name", "tz")
    search_fields = ("name", "tz", "address")


# ---------- Robot (your existing admin) ----------

@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    # keep your previous settings; tweak names to your model
    list_display = ("model", "serial", "site", "tier", "status")
    list_filter = ("site", "tier", "status", "model")
    search_fields = ("serial", "model", "site__name")
    autocomplete_fields = ("site",)
    ordering = ("model", "serial")

