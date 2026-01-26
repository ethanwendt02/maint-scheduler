from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile

User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0  # IMPORTANT: prevents blank extra form that tries to create a new one

# Unregister + reregister User with inline
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)
