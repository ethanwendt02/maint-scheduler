from django.urls import path
from . import views

app_name = "policies"

urlpatterns = [
    path("policy/<int:pk>/pdf/", views.policy_pdf, name="policy_pdf"),
    path("policy/<int:pk>/upload-record/", views.upload_maintenance_record, name="upload_record"),
]
