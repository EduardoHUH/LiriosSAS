from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from appointments.models import Appointment, AppointmentStatus
from appointments.services import (
    CancellationPolicyError,
    InvalidTransitionError,
    ReschedulePolicyError,
    SlotNotAvailableError,
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
    transition_appointment,
)
from catalog.models import Service, ServiceCategory
from core.models import BusinessSettings
from customers.models import Customer
from scheduling.models import BusinessHours

FROZEN_NOW = "2026-09-07 14:00:00"  # 08:00 local (America/Tegucigalpa, UTC-6)


def _today_local():
    return timezone.localtime(timezone.now()).date()


def _at(local_date, hour, minute=0):
    return timezone.make_aware(datetime.combine(local_date, time(hour, minute)))


@pytest.fixture
def category(db):
    return ServiceCategory.objects.create(name="Maquillaje Prueba")


@pytest.fixture
def service(category):
    return Service.objects.create(
        category=category, name="Servicio de prueba", price="500.00", duration_minutes=60
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(full_name="Ana", email="ana@example.com", phone="99999999")


def _bookable_date_with_hours(days_ahead=3):
    target_date = _today_local() + timedelta(days=days_ahead)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="18:00"
    )
    return target_date


# --- transition_appointment (state machine) ---


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_pending_can_transition_to_confirmed(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    transition_appointment(appt, AppointmentStatus.CONFIRMED)

    assert appt.status == AppointmentStatus.CONFIRMED


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_completed_is_a_terminal_state(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.COMPLETED,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    with pytest.raises(InvalidTransitionError):
        transition_appointment(appt, AppointmentStatus.CONFIRMED)


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_cancelling_records_timestamp_and_reason(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    transition_appointment(appt, AppointmentStatus.CANCELLED, reason="Cliente cambió de opinión")

    assert appt.cancelled_at is not None
    assert appt.cancellation_reason == "Cliente cambió de opinión"


# --- create_appointment ---


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_create_appointment_success(service):
    target_date = _bookable_date_with_hours()
    start = _at(target_date, 9)

    appt = create_appointment(
        service=service,
        start_datetime=start,
        customer_data={"full_name": "Ana", "email": "ana@example.com", "phone": "99999999"},
        customer_notes="Alergia al látex",
    )

    assert appt.status == AppointmentStatus.PENDING
    assert appt.price_snapshot == service.price
    assert appt.duration_minutes_snapshot == service.duration_minutes
    assert appt.end_datetime == start + timedelta(minutes=service.duration_minutes)
    assert appt.customer.email == "ana@example.com"


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_create_appointment_reuses_existing_customer_by_email(service):
    existing = Customer.objects.create(
        full_name="Nombre viejo", email="ana@example.com", phone="00000000"
    )
    target_date = _bookable_date_with_hours()

    appt = create_appointment(
        service=service,
        start_datetime=_at(target_date, 9),
        customer_data={"full_name": "Ana López", "email": "ana@example.com", "phone": "99999999"},
    )

    existing.refresh_from_db()
    assert appt.customer_id == existing.id
    assert existing.full_name == "Ana López"
    assert existing.phone == "99999999"
    assert Customer.objects.count() == 1


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_create_appointment_raises_when_slot_unavailable(service):
    target_date = _bookable_date_with_hours()
    start = _at(target_date, 9)
    create_appointment(
        service=service,
        start_datetime=start,
        customer_data={"full_name": "Ana", "email": "ana@example.com", "phone": "99999999"},
    )

    with pytest.raises(SlotNotAvailableError):
        create_appointment(
            service=service,
            start_datetime=start,
            customer_data={"full_name": "Beto", "email": "beto@example.com", "phone": "88888888"},
        )


# --- cancel_appointment ---


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_customer_can_cancel_pending_appointment_regardless_of_deadline(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    cancel_appointment(appt)

    assert appt.status == AppointmentStatus.CANCELLED


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_customer_cannot_cancel_confirmed_appointment_past_deadline(service, customer):
    settings_obj = BusinessSettings.load()
    settings_obj.cancellation_deadline_hours = 24
    settings_obj.save()

    # Appointment starts in 3 hours -- inside the 24h deadline.
    start = timezone.now() + timedelta(hours=3)
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    with pytest.raises(CancellationPolicyError):
        cancel_appointment(appt)

    appt.refresh_from_db()
    assert appt.status == AppointmentStatus.CONFIRMED


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_admin_cancel_bypasses_deadline(service, customer):
    settings_obj = BusinessSettings.load()
    settings_obj.cancellation_deadline_hours = 24
    settings_obj.save()

    start = timezone.now() + timedelta(hours=3)
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    cancel_appointment(appt, enforce_deadline=False)

    assert appt.status == AppointmentStatus.CANCELLED


# --- reschedule_appointment ---


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_reschedule_updates_times_and_increments_count(service, customer):
    target_date = _bookable_date_with_hours()
    old_start = _at(target_date, 9)
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=old_start,
        end_datetime=old_start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    new_start = _at(target_date, 14)

    reschedule_appointment(appt, new_start)

    assert appt.status == AppointmentStatus.CONFIRMED
    assert appt.start_datetime == new_start
    assert appt.end_datetime == new_start + timedelta(minutes=60)
    assert appt.reschedule_count == 1


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_reschedule_only_allowed_from_confirmed(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    with pytest.raises(InvalidTransitionError):
        reschedule_appointment(appt, _at(target_date, 14))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_second_reschedule_is_rejected_by_policy(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
        reschedule_count=1,
    )

    with pytest.raises(ReschedulePolicyError):
        reschedule_appointment(appt, _at(target_date, 14))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_reschedule_past_deadline_is_rejected(service, customer):
    settings_obj = BusinessSettings.load()
    settings_obj.cancellation_deadline_hours = 24
    settings_obj.save()

    start = timezone.now() + timedelta(hours=3)
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    with pytest.raises(ReschedulePolicyError):
        reschedule_appointment(appt, start + timedelta(days=1))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_reschedule_to_taken_slot_raises_slot_not_available(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    other_customer = Customer.objects.create(
        full_name="Beto", email="beto@example.com", phone="88888888"
    )
    Appointment.objects.create(
        customer=other_customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=_at(target_date, 14),
        end_datetime=_at(target_date, 15),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    with pytest.raises(SlotNotAvailableError):
        reschedule_appointment(appt, _at(target_date, 14))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_reschedule_does_not_block_against_its_own_current_slot(service, customer):
    """Rescheduling to a time whose buffer window would otherwise overlap
    the appointment's own current slot must not be rejected as if it
    collided with itself."""
    category = service.category
    buffered_service = Service.objects.create(
        category=category, name="Con buffer", price="100", duration_minutes=30, buffer_minutes=30
    )
    target_date = _bookable_date_with_hours()
    old_start = _at(target_date, 10)
    appt = Appointment.objects.create(
        customer=customer,
        service=buffered_service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=old_start,
        end_datetime=old_start + timedelta(minutes=30),
        price_snapshot=buffered_service.price,
        duration_minutes_snapshot=buffered_service.duration_minutes,
    )
    # 10:15 is inside [10:00, 11:00) -- the old slot's own end+buffer window
    # -- but should still be reachable since it's the appointment's own slot.
    new_start = _at(target_date, 10, 15)

    reschedule_appointment(appt, new_start)

    assert appt.start_datetime == new_start


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_admin_reschedule_bypasses_policy(service, customer):
    target_date = _bookable_date_with_hours()
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
        reschedule_count=1,
    )

    reschedule_appointment(appt, _at(target_date, 14), enforce_policy=False)

    assert appt.reschedule_count == 2
