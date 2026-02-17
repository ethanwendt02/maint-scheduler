from django.urls import path
from .views import metrics_dashboard

urlpatterns = [
    path("", metrics_dashboard, name="metrics_dashboard"),
]
