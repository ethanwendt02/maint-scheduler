from django.urls import path
from . import views

app_name = "policies"

urlpatterns = [
    # ... your existing urls
    path("policy/<int:pk>/upload-record/", views.upload_maintenance_record, name="upload_record"),
]


