from django.contrib import admin

from appointments.models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["customer", "service", "start_datetime", "status"]
    list_filter = ["status", "service"]
    search_fields = ["customer__full_name", "customer__email", "access_token"]
    readonly_fields = ["access_token", "price_snapshot", "duration_minutes_snapshot"]
