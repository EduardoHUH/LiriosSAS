from rest_framework.routers import DefaultRouter

from reviews.views import ReviewPublicViewSet

router = DefaultRouter()
router.register("reviews", ReviewPublicViewSet, basename="public-review")

urlpatterns = router.urls
