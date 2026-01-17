# apps/policies/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import maintenance_policy_pdf

app_name = "policies"

urlpatterns = [
    path("polocoes/<int:pk>/pdf", maintenance_policy_pdf, name="policy_pdf"),
]

