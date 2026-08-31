from datetime import date as date_cls

from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from catalog.models import Service
from scheduling.availability import get_available_slots
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


class AvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        service_slug = request.query_params.get("service")
        if not service_slug:
            return Response(
                {"detail": "Debes especificar un servicio."}, status=400
            )

        date_param = request.query_params.get("date")
        if date_param:
            try:
                target_date = date_cls.fromisoformat(date_param)
            except ValueError:
                return Response(
                    {"detail": "Formato de fecha inválido. Usa AAAA-MM-DD."},
                    status=400,
                )
        else:
            target_date = timezone.localdate()

        try:
            service = Service.objects.select_related("category").get(
                slug=service_slug, is_active=True, category__is_active=True
            )
        except Service.DoesNotExist:
            return Response({"detail": "Servicio no encontrado."}, status=404)

        slots = get_available_slots(service, target_date)
        return Response(
            {
                "service": service.slug,
                "date": target_date.isoformat(),
                "slots": [slot.isoformat() for slot in slots],
            }
        )
