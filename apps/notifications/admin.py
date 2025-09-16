# apps/notifications/admin.py
from django.contrib import admin, messages
from django import forms
from django.db import transaction
import json
from .models import NotificationLog, STATUS_QUEUED

class NotificationLogAdminForm(forms.ModelForm):
    # Human-friendly field instead of raw JSON
    payload_text = forms.CharField(
        label="Payload",
        required=False,
        help_text='Enter JSON (e.g. {"robot":"falcon_x"}) or a comma-separated list (e.g. falcon_x, falcon_y).'
    )

    class Meta:
        model = NotificationLog
        # Hide the real JSON field from the form
        exclude = ["payload"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.payload
        if current not in (None, ""):
            try:
                self.fields["payload_text"].initial = (
                    json.dumps(current, ensure_ascii=False)
                    if isinstance(current, (dict, list)) else str(current)
                )
            except Exception:
                self.fields["payload_text"].initial = str(current)

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("payload_text") or "").strip()
        if not text:
            cleaned["payload"] = {}
            return cleaned

        # 1) JSON
        try:
            cleaned["payload"] = json.loads(text)
            return cleaned
        except json.JSONDecodeError:
            pass

        # 2) CSV -> list
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) > 1:
            cleaned["payload"] = parts
            return cleaned

        # 3) plain string
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
    # ✅ make Django use your custom form
    form = NotificationLogAdminForm

    list_display = ("created_at", "channel", "to", "subject", "status", "sent_at")
    list_filter = ("channel", "status")
    search_fields = ("subject", "message", "to")
    readonly_fields = ("error", "sent_at", "created_at")
    actions = ["send_now"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Auto-send ONLY if it's queued (so edits won't re-send)
        if obj.status == STATUS_QUEUED:
            # Safer: send after the transaction commits
            transaction.on_commit(lambda: self._send_and_flash(request, obj))

    def _send_and_flash(self, request, obj: NotificationLog):
        if obj.send():
            self.message_user(request, "Notification sent ✅", level=messages.SUCCESS)
        else:
            self.message_user(request, f"Notification failed: {obj.error or 'see logs'}", level=messages.ERROR)

    def send_now(self, request, queryset):
        ok = fail = 0
        for obj in queryset:
            if obj.send():
                ok += 1
            else:
                fail += 1
        if ok:
            self.message_user(request, f"Sent {ok} notification(s) ✅", level=messages.SUCCESS)
        if fail:
            self.message_user(request, f"{fail} failed ❌", level=messages.ERROR)

    send_now.short_description = "Send now"
