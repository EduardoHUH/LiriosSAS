from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    StaffTokenObtainPairSerializer,
)
from accounts.throttles import LoginRateThrottle, PasswordResetRateThrottle
from notifications.services import send_password_reset_email

User = get_user_model()


class StaffTokenObtainPairView(TokenObtainPairView):
    serializer_class = StaffTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            }
        )


class PasswordResetRequestView(APIView):
    """Only staff accounts exist in this system (see
    StaffTokenObtainPairSerializer), so only those are matched here.
    Always returns the same generic response regardless of whether the
    email matched an account, to avoid revealing which addresses are
    registered."""

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    GENERIC_RESPONSE = {
        "detail": "Si existe una cuenta con ese correo, se enviará un enlace de recuperación."
    }

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"], is_staff=True, is_active=True
        ).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/restablecer-contrasena/{uid}/{token}/"
            send_password_reset_email(user, reset_url)

        return Response(self.GENERIC_RESPONSE)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = None
        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid, is_staff=True, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            pass

        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "El enlace de recuperación no es válido o expiró."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.save()
        return Response({"detail": "Contraseña actualizada correctamente."})
