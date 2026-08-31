from django.urls import path
from rest_framework.routers import DefaultRouter

from appointments.views import AppointmentCreateView, AppointmentTokenViewSet

router = DefaultRouter()
router.register("appointments", AppointmentTokenViewSet, basename="appointment-token")

urlpatterns = [
    path("appointments/", AppointmentCreateView.as_view(), name="appointment-create"),
] + router.urls
