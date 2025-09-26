# apps/fleet/admin.py
from django.contrib import admin
from django import forms

from apps.policies.models import MaintenancePolicy
from .models import Site, Robot, ClientGroup


# ---------- Inlines shown on Site ----------
class ClientGroupInline(admin.TabularInline):
    model = ClientGroup
    extra = 0
    fields = ("name",)
    show_change_link = True


class PolicyInline(admin.TabularInline):
    model = MaintenancePolicy
    extra = 0
    fields = ("name", "type", "priority", "published")
    show_change_link = True


# ---------- Site (your friendly flags editor preserved) ----------
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
    list_display = ("name", "tz", "group_count", "policy_count")
    search_fields = ("name", "tz", "address")
    ordering = ("name",)
    inlines = [ClientGroupInline, PolicyInline]

    def group_count(self, obj):
        return obj.client_groups.count()
    group_count.short_description = "Groups"

    def policy_count(self, obj):
        return obj.policies.count()
    policy_count.short_description = "Policies"


# ---------- Robot (friendly environments preserved) ----------
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


# ---------- ClientGroup admin ----------
@admin.register(ClientGroup)
class ClientGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "users_count")
    list_select_related = ("site",)
    list_filter = ("site",)
    search_fields = ("name", "site__name")
    filter_horizontal = ("users",)  # nice dual-list selector

    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = "Users"


