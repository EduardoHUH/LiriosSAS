from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from core.models import BusinessSettings
from customers.models import Customer
from scheduling.models import BusinessHours

FROZEN_NOW = "2026-09-07 14:00:00"


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


def _bookable_date_with_hours(days_ahead=3):
    target_date = _today_local() + timedelta(days=days_ahead)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="18:00"
    )
    return target_date


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_create_appointment_success_returns_access_token(service):
    target_date = _bookable_date_with_hours()
    client = APIClient()

    response = client.post(
        "/api/v1/appointments/",
        {
            "service": service.slug,
            "start_datetime": _at(target_date, 9).isoformat(),
            "customer": {
                "full_name": "Ana López",
                "email": "ana@example.com",
                "phone": "99999999",
            },
            "customer_notes": "Alergia al látex",
        },
    )

    assert response.status_code == 201, response.data
    assert response.data["status"] == AppointmentStatus.PENDING
    assert response.data["access_token"]
    assert "admin_notes" not in response.data


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_create_appointment_for_already_taken_slot_returns_400(service):
    target_date = _bookable_date_with_hours()
    start = _at(target_date, 9)
    customer = Customer.objects.create(
        full_name="Beto", email="beto@example.com", phone="88888888"
    )
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=60),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    client = APIClient()

    response = client.post(
        "/api/v1/appointments/",
        {
            "service": service.slug,
            "start_datetime": start.isoformat(),
            "customer": {"full_name": "Ana", "email": "ana@example.com", "phone": "99999999"},
        },
    )

    assert response.status_code == 400
    assert "start_datetime" in response.data


@pytest.mark.django_db
def test_create_appointment_rejects_unknown_service():
    client = APIClient()

    response = client.post(
        "/api/v1/appointments/",
        {
            "service": "no-existe",
            "start_datetime": "2026-09-10T09:00:00-06:00",
            "customer": {"full_name": "Ana", "email": "ana@example.com", "phone": "99999999"},
        },
    )

    assert response.status_code == 400


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_view_appointment_by_token(service):
    target_date = _bookable_date_with_hours()
    customer = Customer.objects.create(
        full_name="Ana", email="ana@example.com", phone="99999999"
    )
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
        admin_notes="Cliente difícil, tener paciencia",
    )
    client = APIClient()

    response = client.get(f"/api/v1/appointments/{appt.access_token}/")

    assert response.status_code == 200
    assert response.data["id"] == appt.id
    assert "admin_notes" not in response.data
    assert "customer" not in response.data


@pytest.mark.django_db
def test_view_appointment_with_wrong_token_404s(service):
    client = APIClient()

    response = client.get("/api/v1/appointments/not-a-real-token/")

    assert response.status_code == 404


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_cancel_appointment_by_token(service):
    target_date = _bookable_date_with_hours()
    customer = Customer.objects.create(
        full_name="Ana", email="ana@example.com", phone="99999999"
    )
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    client = APIClient()

    response = client.post(
        f"/api/v1/appointments/{appt.access_token}/cancel/", {"reason": "Ya no puedo asistir"}
    )

    assert response.status_code == 200
    assert response.data["status"] == AppointmentStatus.CANCELLED


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_cancel_confirmed_appointment_past_deadline_returns_400(service):
    settings_obj = BusinessSettings.load()
    settings_obj.cancellation_deadline_hours = 24
    settings_obj.save()
    customer = Customer.objects.create(
        full_name="Ana", email="ana@example.com", phone="99999999"
    )
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
    client = APIClient()

    response = client.post(f"/api/v1/appointments/{appt.access_token}/cancel/")

    assert response.status_code == 400


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_reschedule_appointment_by_token(service):
    target_date = _bookable_date_with_hours()
    customer = Customer.objects.create(
        full_name="Ana", email="ana@example.com", phone="99999999"
    )
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=_at(target_date, 9),
        end_datetime=_at(target_date, 10),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    client = APIClient()
    new_start = _at(target_date, 14)

    response = client.post(
        f"/api/v1/appointments/{appt.access_token}/reschedule/",
        {"start_datetime": new_start.isoformat()},
    )

    assert response.status_code == 200, response.data
    assert response.data["reschedule_count"] == 1
