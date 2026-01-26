from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile

User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = "user"          # ✅ important, be explicit
    can_delete = False
    extra = 0
    max_num = 1

    def has_add_permission(self, request, obj=None):
        # ✅ if profile already exists, never allow creating another
        if obj and Profile.objects.filter(user=obj).exists():
            return False
        return super().has_add_permission(request, obj)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]
