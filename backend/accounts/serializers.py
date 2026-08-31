from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class StaffTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Only staff accounts may obtain API tokens -- there are no customer
    accounts in this system, so any non-staff user is rejected here as
    defense in depth even though nothing else grants such a user access."""

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            raise AuthenticationFailed(
                "No se encontró una cuenta activa con las credenciales proporcionadas.",
                code="no_active_account",
            )
        return data
