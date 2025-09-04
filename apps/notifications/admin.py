# apps/notifications/admin.py
from django.contrib import admin
from django import forms
import json
from .models import NotificationLog

class NotificationLogAdminForm(forms.ModelForm):
    # Human-friendly field instead of raw JSON
    payload_text = forms.CharField(
        label="Payload",
        required=False,
        help_text="Enter JSON (e.g. {\"robot\":\"falcon_x\"}) "
                  "or a comma-separated list (e.g. falcon_x, falcon_y)."
    )

    class Meta:
        model = NotificationLog
        # Hide the real JSON field from the form
        exclude = ["payload"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.payload
        if current is not None and current != "":
            try:
                # pretty-print existing JSON to the text box
                self.fields["payload_text"].initial = (
                    json.dumps(current, ensure_ascii=False)
                    if isinstance(current, (dict, list))
                    else str(current)
                )
            except Exception:
                self.fields["payload_text"].initial = str(current)

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("payload_text") or "").strip()
        if not text:
            cleaned["payload"] = {}
            return cleaned

        # 1) try JSON first
        try:
            cleaned["payload"] = json.loads(text)
            return cleaned
        except json.JSONDecodeError:
            pass

        # 2) allow comma-separated list => JSON list
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) > 1:
            cleaned["payload"] = parts
            return cleaned

        # 3) fall back to a plain string
        cleaned["payload"] = text
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.payload = self.cleaned_data.get("payload", {})
        if commit:
            obj.save()
        return obj

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    form = NotificationLogAdminForm
    list_display = ("channel", "to", "subject", "status", "created_at")
    search_fields = ("to", "subject")

