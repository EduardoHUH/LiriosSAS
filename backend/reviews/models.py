from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from appointments.models import Appointment
from core.models import TimeStampedModel


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    APPROVED = "approved", "Aprobada"
    REJECTED = "rejected", "Rechazada"


class Review(TimeStampedModel):
    """Verified-only: every review is tied to exactly one completed
    Appointment (enforced at the service-function level, see
    reviews/services.py) -- there is no open/anonymous submission path.
    reviewer_name is a snapshot taken from the appointment's customer at
    creation time, never client-supplied, matching how Appointment itself
    snapshots price/duration rather than dereferencing live data."""

    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="review"
    )
    reviewer_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reviewer_name} ({self.rating}/5)"
