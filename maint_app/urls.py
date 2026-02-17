from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from apps.accounts.views import signup
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
    path("api/calendar/", include("apps.calendarfeed.urls")),
    path("dashboard/", include("apps.dashboard.urls")),


    # Non-API pages
    path("calendar/", include("apps.calendarfeed.urls")),
    path("portal/", include(("apps.portal.urls", "portal"), namespace="portal")),

    # Human-friendly policies routes (site manager links)
    path("policies/", include("apps.policies.urls")),
]

# Serve uploaded media (dev + simple setups)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
