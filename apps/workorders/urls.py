# apps/workorders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkOrderViewSet

router = DefaultRouter()
router.register(r'workorders', WorkOrderViewSet, basename='workorder')

urlpatterns = [
    path("", include(router.urls)),
]
