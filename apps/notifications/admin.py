from django.contrib import admin
from .models import NotificationLog

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "channel", "to", "status", "subject", "sent_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("to", "subject", "message", "error")
    readonly_fields = ("created_at", "sent_at")
