"""Business logic for appointments: the state machine and the
concurrency-safe operations that create, cancel, or reschedule a booking.
Views must go through these functions rather than mutating Appointment
fields directly, so every transition is validated and every slot-touching
change is protected against a concurrent double-booking race."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from core.models import BusinessSettings
from customers.models import Customer
from scheduling.availability import is_slot_available


class SlotNotAvailableError(Exception):
    """Raised when a requested slot is no longer available -- either it
    never was, or a concurrent request just took it."""


class InvalidTransitionError(Exception):
    """Raised when a requested status change isn't allowed from the
    appointment's current status."""


class ReschedulePolicyError(Exception):
    """Raised when a reschedule is structurally valid but against policy
    (already used the one free reschedule, or past the deadline)."""


class CancellationPolicyError(Exception):
    """Raised when a customer-initiated cancellation is past the allowed
    deadline."""


# Explicit state machine: do not allow arbitrary status transitions.
# PENDING -> CONFIRMED covers both a staff-confirmed
# walk-in/phone booking and PixelPay's synchronous online charge (see
# payments/services.py). PENDING -> AWAITING_PAYMENT -> CONFIRMED is not
# currently used by any code path -- it's kept for a future async
# payment method (e.g. bank transfer, or a redirect-based gateway step)
# that needs a distinct "payment in progress" state.
ALLOWED_TRANSITIONS = {
    AppointmentStatus.PENDING: {
        AppointmentStatus.AWAITING_PAYMENT,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.AWAITING_PAYMENT: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.CANCELLED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.RESCHEDULE_REQUESTED,
    },
    AppointmentStatus.RESCHEDULE_REQUESTED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


def transition_appointment(appointment, new_status, *, reason=""):
    allowed = ALLOWED_TRANSITIONS.get(appointment.status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"No se puede cambiar la cita de «{appointment.get_status_display()}» "
            f"a «{AppointmentStatus(new_status).label}»."
        )
    appointment.status = new_status
    if new_status == AppointmentStatus.CANCELLED:
        appointment.cancelled_at = timezone.now()
        appointment.cancellation_reason = reason
    appointment.save()
    return appointment


def _acquire_booking_lock():
    """Global mutex for this (single-resource) salon: locking the
    BusinessSettings singleton row serializes every appointment-creating or
    slot-changing transaction, so a concurrent double-booking race is
    structurally impossible regardless of the gap between an availability
    check and the actual insert/update."""

    BusinessSettings.objects.select_for_update().get(pk=1)


def create_appointment(*, service, start_datetime, customer_data, customer_notes=""):
    with transaction.atomic():
        _acquire_booking_lock()

        if not is_slot_available(service, start_datetime):
            raise SlotNotAvailableError("El horario seleccionado ya no está disponible.")

        customer, _ = Customer.objects.update_or_create(
            email=customer_data["email"],
            defaults={
                "full_name": customer_data["full_name"],
                "phone": customer_data["phone"],
            },
        )

        appointment = Appointment.objects.create(
            customer=customer,
            service=service,
            status=AppointmentStatus.PENDING,
            start_datetime=start_datetime,
            end_datetime=start_datetime + timedelta(minutes=service.duration_minutes),
            price_snapshot=service.price,
            duration_minutes_snapshot=service.duration_minutes,
            customer_notes=customer_notes,
        )
    return appointment


def _cancellation_deadline(appointment):
    hours = BusinessSettings.load().cancellation_deadline_hours
    return appointment.start_datetime - timedelta(hours=hours)


def cancel_appointment(appointment, *, reason="", enforce_deadline=True):
    if enforce_deadline and appointment.status in (
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.RESCHEDULE_REQUESTED,
    ):
        if timezone.now() > _cancellation_deadline(appointment):
            raise CancellationPolicyError(
                "Ya no es posible cancelar esta cita: se superó el plazo permitido."
            )
    return transition_appointment(appointment, AppointmentStatus.CANCELLED, reason=reason)


def reschedule_appointment(appointment, new_start_datetime, *, enforce_policy=True):
    if appointment.status != AppointmentStatus.CONFIRMED:
        raise InvalidTransitionError("Solo se pueden reprogramar citas confirmadas.")

    if enforce_policy:
        if appointment.reschedule_count >= 1:
            raise ReschedulePolicyError(
                "Esta cita ya fue reprogramada anteriormente. Contacta al salón para más cambios."
            )
        if timezone.now() > _cancellation_deadline(appointment):
            raise ReschedulePolicyError(
                "Ya no es posible reprogramar esta cita: se superó el plazo permitido."
            )

    with transaction.atomic():
        _acquire_booking_lock()
        if not is_slot_available(
            appointment.service, new_start_datetime, exclude_appointment_id=appointment.id
        ):
            raise SlotNotAvailableError("El horario seleccionado ya no está disponible.")

        transition_appointment(appointment, AppointmentStatus.RESCHEDULE_REQUESTED)
        appointment.start_datetime = new_start_datetime
        appointment.end_datetime = new_start_datetime + timedelta(
            minutes=appointment.duration_minutes_snapshot
        )
        appointment.reschedule_count += 1
        transition_appointment(appointment, AppointmentStatus.CONFIRMED)
    return appointment
