from rest_framework import serializers

from payments.models import Payment


class PaymentSummarySerializer(serializers.ModelSerializer):
    """Read-only payment summary nested into AppointmentAdminSerializer for
    the admin dashboard's "payment inspection" view. Never used
    customer-facing."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "status_display",
            "amount",
            "currency",
            "paid_at",
            "refunded_amount",
            "pixelpay_payment_uuid",
        ]
        read_only_fields = fields


class CardChargeSerializer(serializers.Serializer):
    """Input for the appointment `pay` action. PixelPay's Sale API takes
    these fields directly (see payments/services.py) -- required billing
    fields below were confirmed empirically against PixelPay's sandbox,
    which rejects a Sale missing any of them."""

    card_number = serializers.CharField(max_length=19)
    card_cvv = serializers.CharField(max_length=4)
    card_expire_month = serializers.IntegerField(min_value=1, max_value=12)
    card_expire_year = serializers.IntegerField(min_value=2000, max_value=2100)
    cardholder = serializers.CharField(max_length=100)

    billing_address = serializers.CharField(max_length=255)
    billing_country = serializers.CharField(max_length=2)
    billing_state = serializers.CharField(max_length=10)
    billing_city = serializers.CharField(max_length=100)
    billing_zip = serializers.CharField(max_length=20)
    billing_phone = serializers.CharField(max_length=30)
