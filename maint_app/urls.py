"""
URL configuration for maint_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
from apps.accounts.views import signup  # if you added signup()
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

app_name = "portal"

urlpatterns = [
    path("", RedirectView.as_view(url="/login/", permanent=False)),  # ← root → /login/
    path("", include("django.contrib.auth.urls")),  # /login/ /logout/ /password_reset/ ...
    path("signup/", signup, name="signup"),

    path("admin/logout/", LogoutView.as_view(next_page="/admin/login/"), name="admin-logout"),
    path("admin/", admin.site.urls),
    path("api/fleet/", include("apps.fleet.urls")),
    path("api/policies/", include("apps.policies.urls")),
    path("api/workorders/", include("apps.workorders.urls")),
    path("api/checklists/", include("apps.checklists.urls")),
    path("calendar/", include("apps.calendarfeed.urls")),
    path("api/calendar/", include("apps.calendarfeed.urls")),
    path("portal/", include(("apps.portal.urls", "portal"), namespace="portal")),
    path("", include("django.contrib.auth.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
