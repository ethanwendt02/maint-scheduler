from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile  # accounts_profile table

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    max_num = 1

    def has_add_permission(self, request, obj=None):
        if obj is None:
            return True
        return not Profile.objects.filter(user=obj).exists()


# If you're editing the built-in auth.User, this must be *that* User model
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]
