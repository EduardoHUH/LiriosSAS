from datetime import datetime, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from scheduling.models import BusinessHours

User = get_user_model()

FROZEN_NOW = "2026-09-07 14:00:00"


def _today_local():
    return timezone.localtime(timezone.now()).date()


def _at(local_date, hour, minute=0):
    return timezone.make_aware(datetime.combine(local_date, time(hour, minute)))


def _bookable_date_with_hours(days_ahead=3):
    target_date = _today_local() + timedelta(days=days_ahead)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="18:00"
    )
    return target_date


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


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


@pytest.fixture
def appointment(service, customer):
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(days=3),
        end_datetime=timezone.now() + timedelta(days=3, hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )


@pytest.mark.django_db
def test_admin_appointments_require_staff():
    client = APIClient()

    response = client.get("/api/v1/admin/appointments/")

    assert response.status_code == 401


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_admin_can_create_a_walk_in_appointment_and_confirm_it_manually(staff_client, service):
    target_date = _bookable_date_with_hours()

    create_response = staff_client.post(
        "/api/v1/admin/appointments/",
        {
            "service": service.slug,
            "start_datetime": _at(target_date, 9).isoformat(),
            "customer": {
                "full_name": "Cliente Walk-in",
                "email": "walkin@example.com",
                "phone": "77777777",
            },
        },
    )
    assert create_response.status_code == 201, create_response.data
    assert create_response.data["status"] == AppointmentStatus.PENDING
    appt_id = create_response.data["id"]

    confirm_response = staff_client.post(f"/api/v1/admin/appointments/{appt_id}/confirm/")

    assert confirm_response.status_code == 200
    assert confirm_response.data["status"] == AppointmentStatus.CONFIRMED


@pytest.mark.django_db
def test_admin_list_filters_by_status(staff_client, appointment):
    other_customer = Customer.objects.create(
        full_name="Beto", email="beto@example.com", phone="88888888"
    )
    Appointment.objects.create(
        customer=other_customer,
        service=appointment.service,
        status=AppointmentStatus.CANCELLED,
        start_datetime=timezone.now() + timedelta(days=5),
        end_datetime=timezone.now() + timedelta(days=5, hours=1),
        price_snapshot=appointment.service.price,
        duration_minutes_snapshot=appointment.service.duration_minutes,
    )

    response = staff_client.get("/api/v1/admin/appointments/?status=confirmed")

    ids = [item["id"] for item in response.data]
    assert appointment.id in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_admin_list_filters_by_customer_email(staff_client, appointment):
    response = staff_client.get("/api/v1/admin/appointments/?customer_email=ana@")

    assert len(response.data) == 1
    assert response.data[0]["id"] == appointment.id


@pytest.mark.django_db
def test_admin_list_ignores_malformed_date_filter_instead_of_500(staff_client, appointment):
    response = staff_client.get("/api/v1/admin/appointments/?date_from=not-a-date")

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_detail_includes_admin_notes_and_customer_contact(staff_client, appointment):
    appointment.admin_notes = "Nota privada"
    appointment.save()

    response = staff_client.get(f"/api/v1/admin/appointments/{appointment.id}/")

    assert response.data["admin_notes"] == "Nota privada"
    assert response.data["customer_email"] == "ana@example.com"


@pytest.mark.django_db
def test_admin_detail_includes_null_payment_when_none_exists(staff_client, appointment):
    response = staff_client.get(f"/api/v1/admin/appointments/{appointment.id}/")

    assert response.data["payment"] is None


@pytest.mark.django_db
def test_admin_detail_includes_payment_summary_when_one_exists(staff_client, appointment):
    from payments.models import Payment, PaymentStatus

    Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
        pixelpay_payment_uuid="S-test-uuid",
    )

    response = staff_client.get(f"/api/v1/admin/appointments/{appointment.id}/")

    assert response.data["payment"]["status"] == PaymentStatus.SUCCEEDED
    assert response.data["payment"]["pixelpay_payment_uuid"] == "S-test-uuid"


@pytest.mark.django_db
def test_admin_patch_can_only_edit_notes_not_status(staff_client, appointment):
    response = staff_client.patch(
        f"/api/v1/admin/appointments/{appointment.id}/",
        {"status": AppointmentStatus.CANCELLED, "admin_notes": "Actualizado"},
    )

    appointment.refresh_from_db()
    assert response.status_code == 200
    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.admin_notes == "Actualizado"


@pytest.mark.django_db
def test_admin_cancel_bypasses_customer_deadline(staff_client, service, customer):
    start = timezone.now() + timedelta(hours=1)
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    response = staff_client.post(f"/api/v1/admin/appointments/{appt.id}/cancel/")

    assert response.status_code == 200
    assert response.data["status"] == AppointmentStatus.CANCELLED


@pytest.mark.django_db
def test_admin_can_mark_completed(staff_client, appointment):
    response = staff_client.post(f"/api/v1/admin/appointments/{appointment.id}/complete/")

    assert response.status_code == 200
    assert response.data["status"] == AppointmentStatus.COMPLETED


@pytest.mark.django_db
def test_admin_can_mark_no_show(staff_client, appointment):
    response = staff_client.post(f"/api/v1/admin/appointments/{appointment.id}/no-show/")

    assert response.status_code == 200
    assert response.data["status"] == AppointmentStatus.NO_SHOW


@pytest.mark.django_db
def test_admin_cannot_complete_a_pending_appointment(staff_client, service, customer):
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=timezone.now() + timedelta(days=1),
        end_datetime=timezone.now() + timedelta(days=1, hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    response = staff_client.post(f"/api/v1/admin/appointments/{appt.id}/complete/")

    assert response.status_code == 400


@pytest.mark.django_db
@freeze_time(FROZEN_NOW)
def test_admin_reschedule_ignores_customer_policy_limits(staff_client, appointment):
    appointment.reschedule_count = 5
    appointment.save()
    target_date = _bookable_date_with_hours()

    response = staff_client.post(
        f"/api/v1/admin/appointments/{appointment.id}/reschedule/",
        {"start_datetime": _at(target_date, 9).isoformat()},
    )

    assert response.status_code == 200, response.data
    assert response.data["reschedule_count"] == 6


@pytest.mark.django_db
def test_admin_destroy_is_not_allowed(staff_client, appointment):
    response = staff_client.delete(f"/api/v1/admin/appointments/{appointment.id}/")

    assert response.status_code == 405
    assert Appointment.objects.filter(id=appointment.id).exists()
