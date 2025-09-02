# apps/policies/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'policies', views.MaintenancePolicyViewSet, basename='policy')

urlpatterns = [
    path("", include(router.urls)),
]

