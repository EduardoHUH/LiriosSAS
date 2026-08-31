from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from scheduling.models import BlockedTime, BusinessHours, SpecialDate
from scheduling.serializers import (
    BlockedTimeAdminSerializer,
    BusinessHoursAdminSerializer,
    BusinessHoursPublicSerializer,
    SpecialDateAdminSerializer,
)


class BusinessHoursPublicViewSet(ReadOnlyModelViewSet):
    serializer_class = BusinessHoursPublicSerializer
    permission_classes = [AllowAny]
    queryset = BusinessHours.objects.filter(is_active=True)


class BusinessHoursAdminViewSet(ModelViewSet):
    serializer_class = BusinessHoursAdminSerializer
    permission_classes = [IsAdminUser]
    queryset = BusinessHours.objects.all()


class SpecialDateAdminViewSet(ModelViewSet):
    serializer_class = SpecialDateAdminSerializer
    permission_classes = [IsAdminUser]
    queryset = SpecialDate.objects.all()


class BlockedTimeAdminViewSet(ModelViewSet):
    serializer_class = BlockedTimeAdminSerializer
    permission_classes = [IsAdminUser]
    queryset = BlockedTime.objects.all()
