from rest_framework import serializers

from reviews.models import Review


class ReviewPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "reviewer_name", "rating", "comment", "created_at"]


class ReviewSummarySerializer(serializers.ModelSerializer):
    """Nested read-only view of a customer's own review on their
    appointment -- lets them see whether it's still pending approval."""

    class Meta:
        model = Review
        fields = ["rating", "comment", "status", "created_at"]
        read_only_fields = fields


class ReviewCreateSerializer(serializers.Serializer):
    """Input for the appointment `review` action. appointment and
    reviewer_name are never client-supplied -- see reviews/services.py."""

    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewAdminSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="appointment.customer.full_name", read_only=True
    )
    service_name = serializers.CharField(
        source="appointment.service.name", read_only=True
    )
    appointment_date = serializers.DateTimeField(
        source="appointment.start_datetime", read_only=True
    )

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = [
            "id",
            "appointment",
            "reviewer_name",
            "rating",
            "comment",
            "moderated_at",
            "moderated_by",
            "created_at",
            "updated_at",
        ]
