# apps/portal/urls.py
from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("tickets/", views.TicketListView.as_view(), name="tickets"),
    path("tickets/new/", views.TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/<int:pk>/", views.TicketDetailView.as_view(), name="ticket_detail"),
    path("policy/", views.PolicyView.as_view(), name="policy"),
    path("admin/tickets/", views.AdminTicketListView.as_view(), name="admin_ticket_list"),
    path("admin/tickets/<int:pk>/", views.AdminTicketDetailView.as_view(), name="admin_ticket_detail"),
    path("portal/", include("apps.portal.urls", namespace="portal")),
]


