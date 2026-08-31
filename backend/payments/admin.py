from django.contrib import admin

from payments.models import Payment, StripeEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["appointment", "amount", "currency", "status", "paid_at"]
    list_filter = ["status"]
    readonly_fields = ["stripe_checkout_session_id", "stripe_payment_intent_id"]


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ["stripe_event_id", "event_type", "created_at"]
    readonly_fields = ["stripe_event_id", "event_type", "payload"]
