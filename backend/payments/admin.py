from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["appointment", "amount", "currency", "status", "paid_at"]
    list_filter = ["status"]
    readonly_fields = ["pixelpay_payment_uuid"]
