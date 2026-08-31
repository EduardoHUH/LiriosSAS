import secrets

from django.db import models

from catalog.models import Service
from core.models import TimeStampedModel
from customers.models import Customer


def generate_access_token():
    return secrets.token_urlsafe(32)


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    AWAITING_PAYMENT = "awaiting_payment", "Esperando pago"
    CONFIRMED = "confirmed", "Confirmada"
    CANCELLED = "cancelled", "Cancelada"
    COMPLETED = "completed", "Completada"
    NO_SHOW = "no_show", "No se presentó"
    RESCHEDULE_REQUESTED = "reschedule_requested", "Reprogramación solicitada"


class Appointment(TimeStampedModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="appointments"
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="appointments"
    )
    status = models.CharField(
        max_length=25,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    # Snapshots taken at booking time so a later change to the service's
    # price or duration never retroactively alters an existing booking.
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes_snapshot = models.PositiveIntegerField()

    access_token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_access_token,
        help_text="Unguessable token used in emailed links for the customer to manage this booking without an account.",
    )

    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(
        blank=True, help_text="Private. Never expose through a public API."
    )

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ["-start_datetime"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F("start_datetime")),
                name="appointment_end_after_start",
            )
        ]
        indexes = [models.Index(fields=["start_datetime", "status"])]

    def __str__(self):
        return f"{self.customer} - {self.service} @ {self.start_datetime}"
