# apps/fleet/admin.py
# apps/fleet/admin.py
from django.contrib import admin
from django import forms

from apps.policies.models import MaintenancePolicy
from .models import Site, Robot, Contact, Payload  # no ClientGroup here

# Try to import ClientGroup if it exists
try:
    from .models import ClientGroup  # optional
    HAS_CLIENT_GROUP = True
except Exception:
    ClientGroup = None  # type: ignore
    HAS_CLIENT_GROUP = False


# ---------- Inlines shown on Site ----------
if HAS_CLIENT_GROUP:
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


# ---------- Site (friendly flags editor + slack_channel) ----------
class SiteAdminForm(forms.ModelForm):
    flags_text = forms.CharField(
        required=False,
        label="Flags",
        help_text="Comma-separated flags (e.g., priority, needs_badge, north).",
    )

    class Meta:
        model = Site
        fields = ["name", "tz", "address", "slack_channel", "flags_text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = getattr(self.instance, "flags", []) or []
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
    list_display = ("name", "tz", "slack_channel", "group_count", "policy_count")
    search_fields = ("name", "tz", "address", "slack_channel")
    ordering = ("name",)
    inlines = [PolicyInline] if not HAS_CLIENT_GROUP else [ClientGroupInline, PolicyInline]

    def group_count(self, obj):
        # Safe even if ClientGroup/related name isn't present
        rel = getattr(obj, "client_groups", None)
        return rel.count() if rel is not None else 0
    group_count.short_description = "Groups"

    def policy_count(self, obj):
        rel = getattr(obj, "policies", None)
        return rel.count() if rel is not None else 0
    policy_count.short_description = "Policies"


# ---------- Robot (friendly environments + new fields) ----------
class RobotAdminForm(forms.ModelForm):
    environments_text = forms.CharField(
        required=False,
        label="Environments",
        help_text="Comma-separated environments (e.g., indoor, warehouse, wet).",
    )

    licenses_text = forms.CharField(
        required=False,
        label="License Numbers",
        help_text="Comma- or semicolon-separated license numbers.",
    )

    class Meta:
        model = Robot
        fields = [
            "model",
            "serial",
            "site",
            "tier",
            "status",
            "robot_type",
            "location",
            "manager",
            "payloads",
            "environments_text",
            "licenses_text",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_env = getattr(self.instance, "environments", []) or []
        if isinstance(current_env, list):
            self.fields["environments_text"].initial = ", ".join(current_env)
        elif isinstance(current_env, dict):
            self.fields["environments_text"].initial = ", ".join(f"{k}:{v}" for k, v in current_env.items())

        current_lic = getattr(self.instance, "licenses", []) or []
        if isinstance(current_lic, list):
            self.fields["licenses_text"].initial = ", ".join(current_lic)

    def clean(self):
        cleaned = super().clean()
        env_text = (cleaned.get("environments_text") or "").strip()
        cleaned["environments"] = [t.strip() for t in env_text.replace(";", ",").split(",") if t.strip()] if env_text else []

        lic_text = (cleaned.get("licenses_text") or "").strip()
        cleaned["licenses"] = [t.strip() for t in lic_text.replace(";", ",").split(",") if t.strip()] if lic_text else []
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.environments = self.cleaned_data.get("environments", [])
        obj.licenses = self.cleaned_data.get("licenses", [])
        if commit:
            obj.save()
        return obj


@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    form = RobotAdminForm
    exclude = ["environments", "licenses"]
    list_display = ("model", "serial", "site", "robot_type", "location", "tier", "status", "manager")
    list_filter = ("site", "tier", "status", "model", "robot_type", "payloads")
    search_fields = ("serial", "model", "site__name", "manager__name", "manager__email")
    autocomplete_fields = ("site", "manager")
    filter_horizontal = ("payloads",)
    ordering = ("model", "serial")


# ---------- Contact & Payload admin ----------
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")
    ordering = ("name",)


@admin.register(Payload)
class PayloadAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    search_fields = ("name", "type")
    ordering = ("name",)


# ---------- ClientGroup admin (only if model exists) ----------
if HAS_CLIENT_GROUP:
    @admin.register(ClientGroup)
    class ClientGroupAdmin(admin.ModelAdmin):
        list_display = ("name", "site", "users_count")
        list_select_related = ("site",)
        list_filter = ("site",)
        search_fields = ("name", "site__name")
        filter_horizontal = ("users",)

        def users_count(self, obj):
            return obj.users.count()
        users_count.short_description = "Users"
