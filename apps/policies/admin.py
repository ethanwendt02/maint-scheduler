# apps/policies/admin.py
from django.contrib import admin
from django import forms
from .models import MaintenancePolicy


def _existing_fields(model, candidates):
    """
    Return a tuple of field names that actually exist on the model.
    (Prevents admin crashes if a field isn't present.)
    """
    model_fields = {f.name for f in model._meta.get_fields()}
    return tuple(f for f in candidates if f in model_fields)


class MaintenancePolicyForm(forms.ModelForm):
    class Meta:
        model = MaintenancePolicy
        fields = "__all__"
        # Tweak/expand help_texts to match your model
        help_texts = {
            "name": "E.g., “Quarterly PM – Spot”.",
            "type": "Preventive / Corrective / Inspection.",
            "priority": "P1 (urgent), P2 (normal), P3 (low).",
            "published": "Enable to start generating work orders.",
            # If these fields exist on your model, the help text will show automatically:
            "site": "Which site this policy applies to.",
            "tier": "Optional: limit to robots at this tier.",
            "robot_type": "Optional: limit to this robot type.",
            "payloads": "Optional: limit to robots with these payloads.",
            "cadence_days": "Time-based cadence (days).",
            "usage_hours": "Usage trigger (hours).",
            "checklist_template": "Attach a checklist template to generate tasks.",
            "manager": "Owner/assignee who is responsible.",
            "sla_hours": "Target completion time in hours.",
            "notify_slack": "Send notifications to the site’s Slack channel.",
        }


@admin.register(MaintenancePolicy)
class MaintenancePolicyAdmin(admin.ModelAdmin):
    form = MaintenancePolicyForm

    # Basic list config (safe if some fields don't exist; Django ignores them in list_display)
    list_display = _existing_fields(
        MaintenancePolicy,
        ("name", "type", "priority", "published"),
    ) or ("name",)
    list_filter = _existing_fields(
        MaintenancePolicy,
        ("type", "priority", "published"),
    )
    search_fields = ("name",)
    ordering = ("-published", "priority", "name")

    # Show our step panels
    change_list_template = "admin/policies/maintenancepolicy/change_list.html"
    change_form_template = "admin/policies/maintenancepolicy/change_form.html"

    # Fieldsets built dynamically so missing fields won't break admin
    def get_fieldsets(self, request, obj=None):
        M = MaintenancePolicy
        basics = _existing_fields(M, ("name", "type", "priority", "published"))
        scope = _existing_fields(M, ("site", "tier", "robot_type", "payloads"))
        triggers = _existing_fields(M, ("cadence_days", "usage_hours"))
        execution = _existing_fields(M, ("checklist_template", "manager"))
        notify_sla = _existing_fields(M, ("sla_hours", "notify_slack"))

        fieldsets = []
        if basics:
            fieldsets.append(("Basics", {"fields": basics}))
        if scope:
            fieldsets.append((
                "Scope",
                {"description": "Pick Site and optional robot filters.",
                 "fields": scope}
            ))
        if triggers:
            fieldsets.append((
                "Triggers",
                {"description": "Choose time and/or usage cadence.",
                 "fields": triggers}
            ))
        if execution:
            fieldsets.append((
                "Execution",
                {"description": "Attach checklist and assign owner.",
                 "fields": execution}
            ))
        if notify_sla:
            fieldsets.append(("Notifications & SLA", {"fields": notify_sla}))
        return tuple(fieldsets)


