# maint_app/urls.py
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from apps.accounts.views import signup  # if you provide signup
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # Root → /login/
    path("", RedirectView.as_view(url="/login/", permanent=False)),

    # Auth: /login/ /logout/ /password_reset/ ...
    path("", include("django.contrib.auth.urls")),

    # Optional signup
    path("signup/", signup, name="signup"),

    # Admin
    path("admin/logout/", LogoutView.as_view(next_page="/admin/login/"), name="admin-logout"),
    path("admin/", admin.site.urls),

    # APIs / other apps
    path("api/fleet/", include("apps.fleet.urls")),
    path("api/policies/", include("apps.policies.urls")),
    path("api/workorders/", include("apps.workorders.urls")),
    path("api/checklists/", include("apps.checklists.urls")),
    path("calendar/", include("apps.calendarfeed.urls")),
    path("api/calendar/", include("apps.calendarfeed.urls")),

    # Client portal (namespaced)
    path("portal/", include(("apps.portal.urls", "portal"), namespace="portal")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

