from rest_framework.routers import DefaultRouter

from catalog.views import ServiceAdminViewSet, ServiceCategoryAdminViewSet

router = DefaultRouter()
router.register("categories", ServiceCategoryAdminViewSet, basename="admin-category")
router.register("services", ServiceAdminViewSet, basename="admin-service")

urlpatterns = router.urls
