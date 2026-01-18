from django.urls import path
from . import views

app_name = "policies"

urlpatterns = [
    path("policy/<int:pk>/pdf/", views.policy_pdf, name="policy_pdf"),
]


