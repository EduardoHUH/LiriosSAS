from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["notification_type", "recipient_email", "status", "sent_at"]
    list_filter = ["notification_type", "status"]
    readonly_fields = ["appointment", "notification_type", "channel", "recipient_email"]
