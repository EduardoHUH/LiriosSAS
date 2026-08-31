from django.urls import path

from payments.views import stripe_webhook

urlpatterns = [
    path("payments/webhook/", stripe_webhook, name="stripe-webhook"),
]
