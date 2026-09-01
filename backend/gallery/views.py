from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from gallery.models import GalleryItem
from gallery.serializers import GalleryItemAdminSerializer, GalleryItemPublicSerializer


class GalleryItemPublicViewSet(ReadOnlyModelViewSet):
    serializer_class = GalleryItemPublicSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = GalleryItem.objects.filter(is_active=True).select_related("category")
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset


class GalleryItemAdminViewSet(ModelViewSet):
    serializer_class = GalleryItemAdminSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = GalleryItem.objects.select_related("category").all()
