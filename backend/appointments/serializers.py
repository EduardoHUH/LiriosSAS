from rest_framework import serializers

from appointments.models import Appointment
from appointments.services import create_appointment
from catalog.models import Service
from catalog.serializers import ServicePublicSerializer
from scheduling.availability import is_slot_available


class CustomerBookingSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30)


class AppointmentCreateSerializer(serializers.Serializer):
    """Shared creation input for both the public booking flow and admin
    walk-in/phone bookings -- both call the same create_appointment()
    service function so the concurrency-safe booking logic is never
    duplicated."""

    service = serializers.SlugField()
    start_datetime = serializers.DateTimeField()
    customer = CustomerBookingSerializer()
    customer_notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_service(self, value):
        try:
            return Service.objects.select_related("category").get(
                slug=value, is_active=True, category__is_active=True
            )
        except Service.DoesNotExist:
            raise serializers.ValidationError("Servicio no encontrado.")

    def validate(self, attrs):
        # A best-effort, friendly check for the common case. The
        # authoritative, race-safe check happens again inside
        # create_appointment() under the booking lock.
        if not is_slot_available(attrs["service"], attrs["start_datetime"]):
            raise serializers.ValidationError(
                {"start_datetime": "El horario seleccionado ya no está disponible."}
            )
        return attrs

    def create(self, validated_data):
        return create_appointment(
            service=validated_data["service"],
            start_datetime=validated_data["start_datetime"],
            customer_data=validated_data["customer"],
            customer_notes=validated_data.get("customer_notes", ""),
        )


class AppointmentCustomerSerializer(serializers.ModelSerializer):
    """Customer-facing view via the appointment's access token. Deliberately
    excludes admin_notes and the Customer record's own fields (
    admin-only notes must never reach a customer-facing endpoint)."""

    service = ServicePublicSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "access_token",
            "service",
            "status",
            "status_display",
            "start_datetime",
            "end_datetime",
            "price_snapshot",
            "customer_notes",
            "reschedule_count",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
        ]
        read_only_fields = fields


class AppointmentRescheduleRequestSerializer(serializers.Serializer):
    start_datetime = serializers.DateTimeField()


class AppointmentCancelRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class AppointmentAdminSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = "__all__"
        # Structural fields only change via the dedicated state-machine
        # actions (confirm/cancel/complete/no_show/reschedule) below, not a
        # generic PATCH -- admin_notes and customer_notes are the only
        # freely editable fields.
        read_only_fields = [
            "id",
            "customer",
            "service",
            "status",
            "start_datetime",
            "end_datetime",
            "price_snapshot",
            "duration_minutes_snapshot",
            "access_token",
            "cancelled_at",
            "cancellation_reason",
            "reschedule_count",
            "created_at",
            "updated_at",
        ]
