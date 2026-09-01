from rest_framework import serializers

from catalog.serializers import ServiceCategoryPublicSerializer
from gallery.models import GalleryItem


class GalleryItemPublicSerializer(serializers.ModelSerializer):
    category = ServiceCategoryPublicSerializer(read_only=True)

    class Meta:
        model = GalleryItem
        fields = ["id", "image", "category", "caption", "display_order"]


class GalleryItemAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryItem
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
