from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from core.models import BusinessSettings
from customers.models import Customer
from scheduling.availability import get_available_slots, is_slot_available
from scheduling.models import BlockedTime, BusinessHours, SpecialDate

# 14:00 UTC = 08:00 local (America/Tegucigalpa is UTC-6, no DST).
FROZEN_NOW = "2026-09-07 14:00:00"


def _today_local():
    return timezone.localtime(timezone.now()).date()


def _at(local_date, hour, minute=0):
    return timezone.make_aware(datetime.combine(local_date, time(hour, minute)))


def _times(slots):
    return [timezone.localtime(s).time().isoformat(timespec="minutes") for s in slots]


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


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_basic_slots_generated_within_business_hours(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )

    slots = get_available_slots(service, target_date)

    assert _times(slots)[0] == "09:00"


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_slot_excluded_if_service_does_not_fit_before_interval_ends(category):
    service = Service.objects.create(
        category=category, name="Servicio 50 min", price="100", duration_minutes=50
    )
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="10:00"
    )

    slots = get_available_slots(service, target_date)

    assert _times(slots) == ["09:00"]


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_confirmed_appointment_blocks_overlapping_slots(service, customer):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 10)
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    times = _times(get_available_slots(service, target_date))

    assert "10:00" not in times
    assert "09:00" in times


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_buffer_time_extends_block_after_appointment(category, customer):
    service = Service.objects.create(
        category=category,
        name="Con buffer",
        price="100",
        duration_minutes=30,
        buffer_minutes=30,
    )
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 10)
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=30),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    times = _times(get_available_slots(service, target_date))

    assert "10:30" not in times
    assert "11:00" in times


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_blocked_time_excludes_slots(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 10)
    BlockedTime.objects.create(
        start_datetime=start, end_datetime=start + timedelta(hours=1), reason="Bloqueo"
    )

    times = _times(get_available_slots(service, target_date))

    assert "10:00" not in times
    assert "09:00" in times


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_special_date_closed_overrides_business_hours(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    SpecialDate.objects.create(date=target_date, is_closed=True, reason="Feriado")

    assert get_available_slots(service, target_date) == []


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_special_date_custom_hours_override_regular_business_hours(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="18:00"
    )
    SpecialDate.objects.create(
        date=target_date,
        is_closed=False,
        special_open_time="09:00",
        special_close_time="10:00",
    )

    times = _times(get_available_slots(service, target_date))

    assert "09:00" in times
    assert "11:00" not in times


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_min_booking_notice_excludes_near_term_slots(service):
    settings_obj = BusinessSettings.load()
    settings_obj.min_booking_notice_hours = 3
    settings_obj.save()

    today = _today_local()
    BusinessHours.objects.create(weekday=today.weekday(), start_time="08:00", end_time="12:00")

    times = _times(get_available_slots(service, today))

    assert "08:00" not in times
    assert "10:00" not in times
    assert "11:00" in times


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_max_booking_window_returns_empty_beyond_window(service):
    settings_obj = BusinessSettings.load()
    settings_obj.max_booking_window_days = 5
    settings_obj.save()

    far_date = _today_local() + timedelta(days=10)
    BusinessHours.objects.create(
        weekday=far_date.weekday(), start_time="09:00", end_time="12:00"
    )

    assert get_available_slots(service, far_date) == []


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_is_accepting_bookings_false_returns_no_slots(service):
    settings_obj = BusinessSettings.load()
    settings_obj.is_accepting_bookings = False
    settings_obj.save()

    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )

    assert get_available_slots(service, target_date) == []


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_non_bookable_service_returns_no_slots(category):
    service = Service.objects.create(
        category=category,
        name="No reservable",
        price="100",
        duration_minutes=30,
        is_bookable=False,
    )
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )

    assert get_available_slots(service, target_date) == []


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_pending_appointment_within_hold_window_blocks_slot(service, customer):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 10)
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    assert "10:00" not in _times(get_available_slots(service, target_date))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_pending_appointment_past_hold_window_does_not_block_slot(service, customer):
    settings_obj = BusinessSettings.load()
    settings_obj.unpaid_hold_minutes = 20
    settings_obj.save()

    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 10)
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    Appointment.objects.filter(pk=appt.pk).update(
        created_at=timezone.now() - timedelta(minutes=30)
    )

    assert "10:00" in _times(get_available_slots(service, target_date))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
@pytest.mark.parametrize(
    "status",
    [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW],
)
def test_non_blocking_statuses_do_not_block_slots(service, customer, status):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 10)
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=status,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    assert "10:00" in _times(get_available_slots(service, target_date))


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_is_slot_available_true_for_offered_slot(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )

    assert is_slot_available(service, _at(target_date, 9)) is True


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_is_slot_available_false_for_booked_slot(service, customer):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    start = _at(target_date, 9)
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    assert is_slot_available(service, start) is False


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_is_slot_available_false_for_off_grid_time(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )

    assert is_slot_available(service, _at(target_date, 9, 7)) is False


@pytest.mark.django_db
def test_availability_endpoint_requires_service_param():
    client = APIClient()

    response = client.get("/api/v1/availability/")

    assert response.status_code == 400


@pytest.mark.django_db
def test_availability_endpoint_rejects_invalid_date_format(service):
    client = APIClient()

    response = client.get(f"/api/v1/availability/?service={service.slug}&date=not-a-date")

    assert response.status_code == 400


@pytest.mark.django_db
def test_availability_endpoint_404s_for_unknown_service():
    client = APIClient()

    response = client.get("/api/v1/availability/?service=no-existe")

    assert response.status_code == 404


@pytest.mark.django_db
def test_availability_endpoint_404s_for_service_in_inactive_category(category):
    category.is_active = False
    category.save()
    service = Service.objects.create(
        category=category, name="Oculto", price="100", duration_minutes=30
    )
    client = APIClient()

    response = client.get(f"/api/v1/availability/?service={service.slug}")

    assert response.status_code == 404


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_availability_endpoint_returns_slots_for_valid_service(service):
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="12:00"
    )
    client = APIClient()

    response = client.get(
        f"/api/v1/availability/?service={service.slug}&date={target_date.isoformat()}"
    )

    assert response.status_code == 200
    assert response.data["service"] == service.slug
    assert len(response.data["slots"]) > 0


@pytest.mark.django_db
def test_availability_endpoint_requires_no_authentication(service):
    client = APIClient()

    response = client.get(f"/api/v1/availability/?service={service.slug}")

    assert response.status_code == 200
