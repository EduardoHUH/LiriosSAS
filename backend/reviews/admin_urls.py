from rest_framework.routers import DefaultRouter

from reviews.views import ReviewAdminViewSet

router = DefaultRouter()
router.register("reviews", ReviewAdminViewSet, basename="admin-review")

urlpatterns = router.urls
