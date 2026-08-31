from django.db import models

from appointments.models import Appointment
from core.models import TimeStampedModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SUCCEEDED = "succeeded", "Exitoso"
    FAILED = "failed", "Fallido"
    REFUNDED = "refunded", "Reembolsado"
    CANCELED = "canceled", "Cancelado"


class Payment(TimeStampedModel):
    """One payment per appointment. Full payment is always required to
    confirm a booking (no deposits, no partial payments in the MVP)."""

    appointment = models.OneToOneField(
        Appointment, on_delete=models.PROTECT, related_name="payment"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="HNL")
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, db_index=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.appointment} - {self.get_status_display()}"


class StripeEvent(TimeStampedModel):
    """Idempotency log for processed Stripe webhook events."""

    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Evento de Stripe"
        verbose_name_plural = "Eventos de Stripe"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.stripe_event_id} ({self.event_type})"
