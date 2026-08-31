from rest_framework.routers import DefaultRouter

from appointments.views import AppointmentAdminViewSet

router = DefaultRouter()
router.register("appointments", AppointmentAdminViewSet, basename="admin-appointment")

urlpatterns = router.urls
