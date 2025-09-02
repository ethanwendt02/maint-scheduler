from django.contrib import admin
from .models import Site, Robot


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "tz", "slack_channel")
    list_filter = ("tz",)
    search_fields = ("name", "slack_channel")
    readonly_fields = ()
    ordering = ("name",)


@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    list_display = ("model", "serial", "site", "tier", "status")
    list_filter = ("site", "tier", "status", "model")
    search_fields = ("serial", "model", "site__name")
    autocomplete_fields = ("site",)
    ordering = ("model", "serial")
