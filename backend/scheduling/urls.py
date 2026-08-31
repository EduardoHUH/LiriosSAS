from rest_framework.routers import DefaultRouter

from scheduling.views import BusinessHoursPublicViewSet

router = DefaultRouter()
router.register("business-hours", BusinessHoursPublicViewSet, basename="public-business-hours")

urlpatterns = router.urls
