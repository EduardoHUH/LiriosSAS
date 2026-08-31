from rest_framework.routers import DefaultRouter

from scheduling.views import (
    BlockedTimeAdminViewSet,
    BusinessHoursAdminViewSet,
    SpecialDateAdminViewSet,
)

router = DefaultRouter()
router.register("business-hours", BusinessHoursAdminViewSet, basename="admin-business-hours")
router.register("special-dates", SpecialDateAdminViewSet, basename="admin-special-date")
router.register("blocked-times", BlockedTimeAdminViewSet, basename="admin-blocked-time")

urlpatterns = router.urls
