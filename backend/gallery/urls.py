from rest_framework.routers import DefaultRouter

from gallery.views import GalleryItemPublicViewSet

router = DefaultRouter()
router.register("gallery", GalleryItemPublicViewSet, basename="public-gallery")

urlpatterns = router.urls
