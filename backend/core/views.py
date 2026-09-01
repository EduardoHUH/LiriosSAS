from datetime import date, timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from core.models import BusinessSettings
from core.serializers import (
    BusinessSettingsAdminSerializer,
    BusinessSettingsPublicSerializer,
    DashboardOverviewSerializer,
    RevenueTrendPointSerializer,
    ServicePopularitySerializer,
)
from core.services import get_dashboard_overview, get_revenue_trend, get_service_popularity


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})


class BusinessSettingsAdminView(generics.RetrieveUpdateAPIView):
    serializer_class = BusinessSettingsAdminSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        return BusinessSettings.load()


class BusinessSettingsPublicView(generics.RetrieveAPIView):
    serializer_class = BusinessSettingsPublicSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return BusinessSettings.load()


@api_view(["GET"])
@permission_classes([IsAdminUser])
def dashboard_overview(request):
    serializer = DashboardOverviewSerializer(get_dashboard_overview())
    return Response(serializer.data)


def _parse_date_range(request):
    today = timezone.localdate()
    date_from_param = request.query_params.get("date_from")
    date_to_param = request.query_params.get("date_to")
    try:
        date_from = date.fromisoformat(date_from_param) if date_from_param else today - timedelta(days=29)
        date_to = date.fromisoformat(date_to_param) if date_to_param else today
    except ValueError:
        return None, None, "Formato de fecha inválido. Usa AAAA-MM-DD."
    return date_from, date_to, None


@api_view(["GET"])
@permission_classes([IsAdminUser])
def revenue_trend(request):
    date_from, date_to, error = _parse_date_range(request)
    if error:
        return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

    group_by = request.query_params.get("group_by", "day")
    if group_by not in ("day", "week", "month"):
        return Response(
            {"detail": "group_by debe ser 'day', 'week' o 'month'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = get_revenue_trend(date_from, date_to, group_by=group_by)
    serializer = RevenueTrendPointSerializer(data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def service_popularity(request):
    date_from, date_to, error = _parse_date_range(request)
    if error:
        return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

    data = get_service_popularity(date_from, date_to)
    serializer = ServicePopularitySerializer(data, many=True)
    return Response(serializer.data)
