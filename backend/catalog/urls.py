from rest_framework.routers import DefaultRouter

from catalog.views import ServiceCategoryPublicViewSet, ServicePublicViewSet

router = DefaultRouter()
router.register("categories", ServiceCategoryPublicViewSet, basename="public-category")
router.register("services", ServicePublicViewSet, basename="public-service")

urlpatterns = router.urls
