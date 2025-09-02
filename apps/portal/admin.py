# apps/portal/admin.py
from django.contrib import admin
from .models import Organization, ClientProfile, ClientTicket, TicketComment


admin.site.site_header = "Field AI — Admin"
admin.site.site_title = "Field AI Admin"
admin.site.index_title = "Operations Dashboard"

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name",)

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")
    list_filter = ("organization", "role")
    search_fields = ("user__username", "organization__name")

@admin.register(ClientTicket)
class ClientTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "organization", "created_by",
                    "priority", "status", "created_at")
    list_filter = ("organization", "priority", "status", "created_at")
    search_fields = ("subject", "description", "created_by__username")
    autocomplete_fields = ("organization", "created_by")

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("ticket__subject", "author__username", "body")

