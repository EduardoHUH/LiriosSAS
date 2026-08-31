from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from catalog.models import Service, ServiceCategory
from catalog.serializers import (
    ServiceAdminSerializer,
    ServiceCategoryAdminSerializer,
    ServiceCategoryPublicSerializer,
    ServicePublicSerializer,
)
from core.mixins import ProtectedDeleteMixin


class ServiceCategoryPublicViewSet(ReadOnlyModelViewSet):
    serializer_class = ServiceCategoryPublicSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    queryset = ServiceCategory.objects.filter(is_active=True)


class ServicePublicViewSet(ReadOnlyModelViewSet):
    serializer_class = ServicePublicSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Service.objects.filter(
            is_active=True, category__is_active=True
        ).select_related("category")
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset


class ServiceCategoryAdminViewSet(ProtectedDeleteMixin, ModelViewSet):
    serializer_class = ServiceCategoryAdminSerializer
    permission_classes = [IsAdminUser]
    queryset = ServiceCategory.objects.all()
    protected_delete_message = (
        "No se puede eliminar esta categoría porque tiene servicios asociados."
    )


class ServiceAdminViewSet(ProtectedDeleteMixin, ModelViewSet):
    serializer_class = ServiceAdminSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Service.objects.select_related("category").all()
    protected_delete_message = (
        "No se puede eliminar este servicio porque tiene citas asociadas."
    )
