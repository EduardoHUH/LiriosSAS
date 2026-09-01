from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from reviews.models import Review, ReviewStatus
from reviews.serializers import ReviewAdminSerializer, ReviewPublicSerializer


class ReviewPublicViewSet(ReadOnlyModelViewSet):
    serializer_class = ReviewPublicSerializer
    permission_classes = [AllowAny]
    queryset = Review.objects.filter(status=ReviewStatus.APPROVED)


class ReviewAdminViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewAdminSerializer
    permission_classes = [IsAdminUser]
    queryset = Review.objects.select_related(
        "appointment", "appointment__customer", "appointment__service"
    )

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Las reseñas solo se crean desde la cita del cliente."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["post"], url_path="approve")
    def approve(self, request):
        return self._moderate(request, ReviewStatus.APPROVED)

    @action(detail=False, methods=["post"], url_path="reject")
    def reject(self, request):
        return self._moderate(request, ReviewStatus.REJECTED)

    def _moderate(self, request, new_status):
        ids = request.data.get("ids", [])
        updated = Review.objects.filter(id__in=ids).update(
            status=new_status, moderated_at=timezone.now(), moderated_by=request.user
        )
        return Response({"updated": updated})
