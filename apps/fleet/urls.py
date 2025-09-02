# apps/fleet/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'robots', views.RobotViewSet, basename='robot')
router.register(r'sites', views.SiteViewSet, basename='site')

urlpatterns = [path("", include(router.urls))]
