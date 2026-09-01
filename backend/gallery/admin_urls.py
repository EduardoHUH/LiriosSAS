from rest_framework.routers import DefaultRouter

from gallery.views import GalleryItemAdminViewSet

router = DefaultRouter()
router.register("gallery", GalleryItemAdminViewSet, basename="admin-gallery")

urlpatterns = router.urls
