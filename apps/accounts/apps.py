from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"     # ← IMPORTANT: full package path
    verbose_name = "Accounts"


