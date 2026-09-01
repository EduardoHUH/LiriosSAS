from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from core.models import BusinessSettings
from core.serializers import (
    BusinessSettingsAdminSerializer,
    BusinessSettingsPublicSerializer,
    DashboardOverviewSerializer,
)
from core.services import get_dashboard_overview


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
