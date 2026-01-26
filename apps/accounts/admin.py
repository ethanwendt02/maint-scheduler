from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model

from .models import Profile  # your OneToOne profile model

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = "user"      # make it explicit
    extra = 0             # IMPORTANT: no blank “extra” row
    max_num = 1           # IMPORTANT: only one profile allowed
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """
        Allow adding ONLY if the user has no profile yet.
        Prevents the admin from trying to add a second profile.
        """
        if obj is None:
            return True
        return not hasattr(obj, "profile")


# Unregister/Register User admin with inline attached
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]
