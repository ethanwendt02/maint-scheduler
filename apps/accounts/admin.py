from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = "user"
    can_delete = False
    extra = 0
    max_num = 1

    def has_add_permission(self, request, obj=None):
        # If a profile already exists, do NOT allow creating another one
        if obj and Profile.objects.filter(user=obj).exists():
            return False
        return super().has_add_permission(request, obj)


class UserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]


# ✅ unregister whatever is currently registered, then register ours
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, UserAdmin)


# Optional: manage Profiles directly too (handy for Slack IDs)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "slack_user_id")
    search_fields = ("user__username", "user__email", "slack_user_id")
