from rest_framework import serializers

from core.models import BusinessSettings


class BusinessSettingsAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSettings
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class BusinessSettingsPublicSerializer(serializers.ModelSerializer):
    """Curated subset of BusinessSettings safe to expose to the public
    website -- excludes reminder_hours_before (internal scheduling detail)
    and the timestamp/id fields, alongside every other admin-only field."""

    class Meta:
        model = BusinessSettings
        fields = [
            "business_name",
            "contact_email",
            "contact_phone",
            "address",
            "social_links",
            "min_booking_notice_hours",
            "max_booking_window_days",
            "cancellation_deadline_hours",
            "unpaid_hold_minutes",
            "default_buffer_minutes",
            "is_accepting_bookings",
        ]


class DashboardOverviewSerializer(serializers.Serializer):
    """Not a ModelSerializer -- this is a plain aggregate, not one model's
    fields. DecimalField (rather than a bare float) matters here the same
    way it does everywhere else in this codebase: money is never floats."""

    appointments_today = serializers.IntegerField()
    upcoming_appointments_next_7_days = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_appointments_this_month = serializers.IntegerField()
    cancellations_this_month = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    refund_pending_payments = serializers.IntegerField()
