from django.contrib import admin
from django import forms
from .models import ChecklistTemplate, ChecklistRun
from django.utils.text import slugify
from datetime import date

# ---------- Template (authoring) ----------

class ChecklistTemplateForm(forms.ModelForm):
    items_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="One checklist step per line."
    )
    kit_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="One tool per line (maintenance kit)."
    )

    class Meta:
        model = ChecklistTemplate
        fields = ["checklist_id", "name", "version", "items_text", "kit_text", "requires_photos"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.instance.items, list):
            self.fields["items_text"].initial = "\n".join(self.instance.items)
        if isinstance(self.instance.kit, list):
            self.fields["kit_text"].initial = "\n".join(self.instance.kit)

    def clean(self):
        cleaned = super().clean()
        items_lines = cleaned.get("items_text", "").splitlines()
        kit_lines   = cleaned.get("kit_text", "").splitlines()
        cleaned["items"] = [s.strip() for s in items_lines if s.strip()]
        cleaned["kit"]   = [s.strip() for s in kit_lines if s.strip()]
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.items = self.cleaned_data.get("items", [])
        obj.kit   = self.cleaned_data.get("kit", [])
        if commit:
            obj.save()
        return obj


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    form = ChecklistTemplateForm
    exclude = ("items", "kit")
    list_display = ("checklist_id", "name", "version", "requires_photos")
    search_fields = ("checklist_id", "name")


# ---------- Run (execution) with checkboxes ----------

class ChecklistRunForm(forms.ModelForm):
    """
    Build BooleanFields at runtime from the selected template's items & kit.
    Results go into responses (dict) and tools_used (list).
    """
    class Meta:
        model = ChecklistRun
        fields = ["work_order", "template", "notes", "signed_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Determine the template either from POSTed value or from the instance
        tmpl = None
        data = self.data or None
        if data and data.get("template"):
            try:
                tmpl = ChecklistTemplate.objects.get(pk=data.get("template"))
            except ChecklistTemplate.DoesNotExist:
                tmpl = None
        elif self.instance and self.instance.pk:
            tmpl = self.instance.template

        # Use existing responses/tools on edit
        existing_resp  = self.instance.responses if getattr(self.instance, "responses", None) else {}
        existing_tools = set(self.instance.tools_used or [])

        # Dynamically add a checkbox for each item
        if tmpl:
            for idx, label in enumerate(tmpl.items or []):
                field_name = f"step__{idx}"
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=label,
                    initial=bool(existing_resp.get(label, False)),
                )

            # And a checkbox for each tool in the kit
            for idx, tool in enumerate(tmpl.kit or []):
                field_name = f"tool__{idx}"
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=f"Tool: {tool}",
                    initial=(tool in existing_tools),
                )

    def clean(self):
        cleaned = super().clean()

        # Reconstruct responses/tools_used from the dynamic fields
        tmpl = cleaned.get("template")
        responses = {}
        tools_used = []
        if tmpl:
            for idx, label in enumerate(tmpl.items or []):
                if self.cleaned_data.get(f"step__{idx}"):
                    responses[label] = True
                else:
                    responses[label] = False

            for idx, tool in enumerate(tmpl.kit or []):
                if self.cleaned_data.get(f"tool__{idx}"):
                    tools_used.append(tool)

        cleaned["responses"] = responses
        cleaned["tools_used"] = tools_used
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.responses = self.cleaned_data.get("responses", {})
        obj.tools_used = self.cleaned_data.get("tools_used", [])

        # Optional: stamp Robot.last_maintained if all steps are completed
        try:
            wo = obj.work_order
            robot = getattr(wo, "robot", None)
            all_done = all(obj.responses.values()) if obj.responses else False
            if robot and all_done:
                robot.last_maintained = date.today()
                robot.save(update_fields=["last_maintained"])
        except Exception:
            pass

        if commit:
            obj.save()
        return obj


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    form = ChecklistRunForm
    exclude = ["responses", "tools_used", "photos"]  # hide raw JSON
    list_display = ("id", "template", "work_order", "created_at")
    autocomplete_fields = ("work_order", "signed_by")
