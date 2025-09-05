from django import forms
from .models import MaintenancePolicy

class MaintenancePolicyForm(forms.ModelForm):
    scope_text = forms.CharField(
        required=False,
        help_text="Comma-separated scope values (e.g., spot_x, spot_y)."
    )
    threshold_text = forms.CharField(
        required=False,
        help_text="Key:Value pairs (e.g., battery:80, motor:90)."
    )

    class Meta:
        model = MaintenancePolicy
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.instance.scope, list):
            self.fields["scope_text"].initial = ", ".join(self.instance.scope)
        if isinstance(self.instance.threshold, dict):
            self.fields["threshold_text"].initial = ", ".join(f"{k}:{v}" for k, v in self.instance.threshold.items())

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get("scope_text", "")
        cleaned["scope"] = [s.strip() for s in scope.split(",") if s.strip()]

        threshold = {}
        for pair in cleaned.get("threshold_text", "").split(","):
            if ":" in pair:
                k, v = pair.split(":", 1)
                threshold[k.strip()] = v.strip()
        cleaned["threshold"] = threshold
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.scope = self.cleaned_data.get("scope", [])
        obj.threshold = self.cleaned_data.get("threshold", {})
        if commit:
            obj.save()
        return obj

@admin.register(MaintenancePolicy)
class MaintenancePolicyAdmin(admin.ModelAdmin):
    form = MaintenancePolicyForm
    exclude = ["scope", "threshold"]

