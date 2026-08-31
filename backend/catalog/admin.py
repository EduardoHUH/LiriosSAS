from django.contrib import admin

from catalog.models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "is_active"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "duration_minutes", "is_active", "is_bookable"]
    list_filter = ["category", "is_active", "is_bookable"]
    prepopulated_fields = {"slug": ["name"]}
