"""Business logic for reviews: a review is always verified against a
completed Appointment, never accepted as an open/anonymous submission.
Views go through this module rather than creating Review rows directly."""

from django.db import IntegrityError

from appointments.models import AppointmentStatus
from reviews.models import Review


class ReviewNotAllowedError(Exception):
    """Raised when an appointment isn't eligible for a review yet (not
    completed) or already has one."""


def create_review_for_appointment(appointment, *, rating, comment):
    if appointment.status != AppointmentStatus.COMPLETED:
        raise ReviewNotAllowedError(
            "Solo puedes dejar una reseña para una cita completada."
        )

    # Friendly pre-check; the OneToOneField's DB-level uniqueness is the
    # authoritative backstop against a race (two near-simultaneous
    # submissions for the same appointment).
    if Review.objects.filter(appointment=appointment).exists():
        raise ReviewNotAllowedError("Ya dejaste una reseña para esta cita.")

    try:
        return Review.objects.create(
            appointment=appointment,
            reviewer_name=appointment.customer.full_name,
            rating=rating,
            comment=comment,
        )
    except IntegrityError:
        raise ReviewNotAllowedError("Ya dejaste una reseña para esta cita.") from None
