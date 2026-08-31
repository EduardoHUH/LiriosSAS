from django.db import models

from appointments.models import Appointment
from core.models import TimeStampedModel


class NotificationType(models.TextChoices):
    BOOKING_CONFIRMATION = "booking_confirmation", "Confirmación de reserva"
    PAYMENT_CONFIRMATION = "payment_confirmation", "Confirmación de pago"
    CANCELLATION = "cancellation", "Cancelación"
    RESCHEDULE = "reschedule", "Reprogramación"
    REMINDER = "reminder", "Recordatorio"
    ADMIN_ALERT = "admin_alert", "Alerta administrativa"
    PASSWORD_RESET = "password_reset", "Restablecimiento de contraseña"


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Correo electrónico"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SENT = "sent", "Enviado"
    FAILED = "failed", "Fallido"


class Notification(TimeStampedModel):
    """Log of outbound notifications. Kept decoupled from booking/payment
    business logic (a channel is just a field here) so a channel like
    WhatsApp or SMS can be added later without touching that logic."""

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    channel = models.CharField(
        max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.EMAIL
    )
    recipient_email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING
    )
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.recipient_email}"
