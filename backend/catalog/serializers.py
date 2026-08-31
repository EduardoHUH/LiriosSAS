from rest_framework import serializers

from catalog.models import Service, ServiceCategory


class ServiceCategoryPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "slug", "description", "display_order"]


class ServicePublicSerializer(serializers.ModelSerializer):
    category = ServiceCategoryPublicSerializer(read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "duration_minutes",
            "image",
            "preparation_instructions",
            "cancellation_policy_notes",
            "is_bookable",
            "display_order",
            "category",
        ]


class ServiceCategoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ServiceAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
