from django.contrib import admin

from scheduling.models import BlockedTime, BusinessHours, SpecialDate


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ["get_weekday_display", "start_time", "end_time", "is_active"]
    list_filter = ["weekday", "is_active"]


@admin.register(SpecialDate)
class SpecialDateAdmin(admin.ModelAdmin):
    list_display = ["date", "is_closed", "reason"]


@admin.register(BlockedTime)
class BlockedTimeAdmin(admin.ModelAdmin):
    list_display = ["start_datetime", "end_datetime", "reason"]
