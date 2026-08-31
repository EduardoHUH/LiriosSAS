from django.db import models

from appointments.models import Appointment
from core.models import TimeStampedModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SUCCEEDED = "succeeded", "Exitoso"
    FAILED = "failed", "Fallido"
    REFUND_PENDING = "refund_pending", "Reembolso pendiente"
    REFUNDED = "refunded", "Reembolsado"
    CANCELED = "canceled", "Cancelado"


class Payment(TimeStampedModel):
    """One payment per appointment. Full payment is always required to
    confirm a booking online (no deposits, no partial payments in the
    MVP). Paying online is itself optional -- a customer may instead
    leave the appointment pending for staff to confirm without payment.

    Refunds are not automated: PixelPay requires a 128-character
    void_signature whose derivation isn't documented anywhere reachable
    (see payments/services.py), so a cancelled paid appointment is
    flagged refund_pending for the salon owner to refund manually from
    the PixelPay merchant dashboard, then marked refunded here by hand."""

    appointment = models.OneToOneField(
        Appointment, on_delete=models.PROTECT, related_name="payment"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="HNL")
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    pixelpay_payment_uuid = models.CharField(
        max_length=64, blank=True, db_index=True, help_text="PixelPay transaction reference."
    )

    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.appointment} - {self.get_status_display()}"
