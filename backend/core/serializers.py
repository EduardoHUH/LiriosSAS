from rest_framework import serializers

from core.models import BusinessSettings


class BusinessSettingsAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSettings
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


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
