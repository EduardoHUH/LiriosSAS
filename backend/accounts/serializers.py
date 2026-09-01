from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class StaffTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Only staff accounts may obtain API tokens -- there are no customer
    accounts in this system, so any non-staff user is rejected here as
    defense in depth even though nothing else grants such a user access.

    Overrides SimpleJWT's default_error_messages so every failure path --
    wrong password, a nonexistent username, or a valid non-staff account --
    shows the same Spanish message. Without this, SimpleJWT's own
    credential check (inside super().validate() below) raises its English
    default before this serializer's own staff check ever runs; DRF
    merges default_error_messages from the whole MRO into self.error_messages
    before validate() runs, so overriding the dict here is enough --
    SimpleJWT's raise already reads the overridden value."""

    default_error_messages = {
        "no_active_account": "No se encontró una cuenta activa con las credenciales proporcionadas.",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"], code="no_active_account"
            )
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
