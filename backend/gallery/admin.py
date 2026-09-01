from django.contrib import admin
from django.utils.html import format_html

from gallery.models import GalleryItem


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ["image_preview", "caption", "category", "display_order", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["caption"]

    @admin.display(description="Vista previa")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="height: 48px; border-radius: 4px;">', obj.image.url
        )
