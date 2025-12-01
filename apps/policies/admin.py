# apps/policies/admin.py
from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
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


def _template_preview_html(policy: MaintenancePolicy) -> str:
    """
    Build an HTML ordered list of the attached checklist template's items.
    Shows order, text, and optional kit items.
    """
    if not policy or not getattr(policy, "pk", None):
        return "Save policy to preview template steps."
    tmpl = getattr(policy, "checklist_template", None)
    if not tmpl:
        return "No checklist template attached."

    # Expect a related name like `items` on the template; adjust if yours differs.
    items_qs = getattr(tmpl, "items", None)
    if not items_qs:
        return "This checklist template has no items."
    items = items_qs.all().order_by("order", "id")

    if not items:
        return "This checklist template has no items."

    rows = []
    for it in items:
        kit = getattr(it, "kit_items", "") or ""
        kit_html = f' <em style="color:#666;">(kit: {kit})</em>' if kit else ""
        order = getattr(it, "order", 0)
        text = getattr(it, "text", "")
        rows.append(f"<li>#{order} {text}{kit_html}</li>")

    return mark_safe(f"<ol>{''.join(rows)}</ol>")


@admin.register(MaintenancePolicy)
class MaintenancePolicyAdmin(admin.ModelAdmin):
    form = MaintenancePolicyForm

    # Columns in the changelist
    list_display = _existing_fields(
        MaintenancePolicy,
        ("name", "site", "assigned_to", "checklist_template"),
    ) or ("name",)

    list_filter = _existing_fields(
        MaintenancePolicy,
        ("site", "assigned_to", "robots", "payloads"),
    )

    search_fields = ("name", "site__name", "assigned_to__username")
    ordering = ("name",)  # old ("-published", "priority", "name") would now break

    # Keep your custom templates
    change_list_template = "admin/policies/maintenancepolicy/change_list.html"
    change_form_template = "admin/policies/maintenancepolicy/change_form.html"

    # Show the preview as a readonly field
    readonly_fields = ("_template_preview",)

    # Helpful for M2M
    filter_horizontal = ("robots", "payloads")

    def get_fieldsets(self, request, obj=None):
        M = MaintenancePolicy

        # Basic info
        basics = _existing_fields(M, ("name", "site", "assigned_to"))

        # Scope: which robots/payloads this policy applies to
        scope = _existing_fields(M, ("robots", "payloads"))

        # Execution: template + preview
        execution = _existing_fields(M, ("checklist_template",))

        fieldsets = []

        if basics:
            fieldsets.append((
                "Basics",
                {"fields": basics},
            ))

        if scope:
            fieldsets.append((
                "Scope",
                {
                    "description": "Pick which robots and payloads this policy applies to.",
                    "fields": scope,
                },
            ))

        # Inject preview into Execution section
        exec_fields = list(execution) if execution else []
        if "checklist_template" in exec_fields:
            idx = exec_fields.index("checklist_template") + 1
            exec_fields.insert(idx, "_template_preview")
        else:
            exec_fields.append("_template_preview")

        fieldsets.append((
            "Execution",
            {
                "description": "Attach a checklist template and see a live preview of steps.",
                "fields": tuple(exec_fields),
            },
        ))

        return tuple(fieldsets)

    def _template_preview(self, obj):
        return _template_preview_html(obj)

    _template_preview.short_description = "Checklist steps preview"
