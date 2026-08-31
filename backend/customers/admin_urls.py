from rest_framework.routers import DefaultRouter

from customers.views import CustomerAdminViewSet

router = DefaultRouter()
router.register("customers", CustomerAdminViewSet, basename="admin-customer")

urlpatterns = router.urls
