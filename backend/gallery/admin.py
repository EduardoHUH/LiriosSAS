from django.contrib import admin

from gallery.models import GalleryItem


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ["caption", "category", "display_order", "is_active"]
    list_filter = ["category", "is_active"]
