from rest_framework import serializers

from customers.models import Customer


class CustomerAdminSerializer(serializers.ModelSerializer):
    appointment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "admin_notes",
            "appointment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "appointment_count", "created_at", "updated_at"]
