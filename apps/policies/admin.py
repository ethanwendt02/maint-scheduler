# apps/policies/admin.py
from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from .models import MaintenancePolicy
from django.urls import path,reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .pdf import generate_policy_pdf
from .models import MaintenanceRecord




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

class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0
    fields = ("uploaded_at", "uploaded_by", "file", "notes")
    readonly_fields = ("uploaded_at", "uploaded_by")


@admin.register(MaintenancePolicy)
class MaintenancePolicyAdmin(admin.ModelAdmin):
    inlines = [MaintenanceRecordInline]

    form = MaintenancePolicyForm
    

    list_display = _existing_fields(
        MaintenancePolicy,
        ("name", "type", "priority", "owner", "owner_group", "published"),
    ) or ("name",)
    list_filter = _existing_fields(
        MaintenancePolicy,
        ("type", "priority", "owner_group", "published"),
    )
    search_fields = ("name",)

    # handy for robots/payloads
    filter_horizontal = _existing_fields(
        MaintenancePolicy,
        ("robots", "payloads"),
    )

    readonly_fields = ("download_pdf_button", "_template_preview",)

    def get_fieldsets(self, request, obj=None):
        M = MaintenancePolicy
        basics = _existing_fields(M, ("name", "type", "priority", "published"))
        scope = _existing_fields(M, ("site", "robots", "payloads"))
        triggers = _existing_fields(M, ("interval_days", "window_days", "counter"))
        execution = _existing_fields(
            M,
            ("checklist_template", "owner", "owner_group"),
        )
        notify_sla = _existing_fields(M, ("sla_hours", "notify_slack"))

        fieldsets = []
        if basics:
            fieldsets.append(("Basics", {"fields": basics}))
        if scope:
            fieldsets.append(("Scope", {"fields": scope}))
        if triggers:
            fieldsets.append(("Triggers", {"fields": triggers}))

        exec_fields = list(execution) if execution else []
        exec_fields.insert(0, "download_pdf_button")

        if "checklist_template" in exec_fields:
            idx = exec_fields.index("checklist_template") + 1
            exec_fields.insert(idx, "_template_preview")
        else:
            exec_fields.append("_template_preview")
        fieldsets.append(("Execution", {"fields": tuple(exec_fields)}))

        if notify_sla:
            fieldsets.append(("Notifications & SLA", {"fields": notify_sla}))

        return tuple(fieldsets)

        # --- PDF button + endpoint ---

    def download_pdf_button(self, obj):
        if not obj or not obj.pk:
            return "Save to enable PDF download"

        url = reverse("admin:policies_maintenancepolicy_pdf", args=[obj.pk])
        return mark_safe(f'<a class="button" href="{url}">Download Policy PDF</a>')

    download_pdf_button.short_description = "Policy PDF"

    def download_pdf(self, request, pk):
        policy = get_object_or_404(MaintenancePolicy, pk=pk)
        pdf_bytes = generate_policy_pdf(policy)

        # If your generator returns BytesIO, convert to bytes
        if hasattr(pdf_bytes, "getvalue"):
            pdf_bytes = pdf_bytes.getvalue()

        filename = f"maintenance_policy_{policy.pk}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/pdf/",
                self.admin_site.admin_view(self.download_pdf),
                name="policies_maintenancepolicy_pdf",
            ),
        ]
        return custom_urls + urls



    def _template_preview(self, obj):
        return _template_preview_html(obj)

    _template_preview.short_description = "Checklist steps preview"

