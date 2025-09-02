# apps/checklists/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChecklistTemplateViewSet, ChecklistRunViewSet

router = DefaultRouter()
router.register(r'templates', ChecklistTemplateViewSet, basename='checklist-template')
router.register(r'runs', ChecklistRunViewSet, basename='checklist-run')

urlpatterns = [
    path("", include(router.urls)),
]

