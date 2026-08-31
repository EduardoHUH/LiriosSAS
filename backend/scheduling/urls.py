from django.urls import path
from rest_framework.routers import DefaultRouter

from scheduling.views import AvailabilityView, BusinessHoursPublicViewSet

router = DefaultRouter()
router.register("business-hours", BusinessHoursPublicViewSet, basename="public-business-hours")

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
] + router.urls
