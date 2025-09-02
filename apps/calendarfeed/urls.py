from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ics_feed, UpcomingEventsViewSet

router = DefaultRouter()
router.register(r'events', UpcomingEventsViewSet, basename='calendar-events')

urlpatterns = [
    path("<str:token>.ics", ics_feed, name="calendar-ics"),
    path("", include(router.urls)),
]
