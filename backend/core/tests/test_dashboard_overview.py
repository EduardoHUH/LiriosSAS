from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer

User = get_user_model()

URL = "/api/v1/admin/dashboard/overview/"


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def customer(db):
    return Customer.objects.create(full_name="Ana López", email="ana@example.com", phone="99999999")


@pytest.fixture
def service(db):
    category = ServiceCategory.objects.create(name="Maquillaje Prueba")
    return Service.objects.create(
        category=category, name="Servicio de prueba", price="500.00", duration_minutes=60
    )


def _appointment(service, customer, *, status, start_datetime, cancelled_at=None):
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=status,
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
        cancelled_at=cancelled_at,
    )


@pytest.mark.django_db
def test_requires_staff():
    client = APIClient()

    response = client.get(URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_counts_appointment_today_but_excludes_cancelled(service, customer, staff_client):
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now)
    _appointment(
        service, customer, status=AppointmentStatus.CANCELLED, start_datetime=now, cancelled_at=now
    )

    response = staff_client.get(URL)

    assert response.data["appointments_today"] == 1


@pytest.mark.django_db
def test_counts_confirmed_upcoming_within_7_days_only(service, customer, staff_client):
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now + timedelta(days=3))
    _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now + timedelta(days=20))
    _appointment(service, customer, status=AppointmentStatus.PENDING, start_datetime=now + timedelta(days=3))

    response = staff_client.get(URL)

    assert response.data["upcoming_appointments_next_7_days"] == 1


@pytest.mark.django_db
def test_revenue_this_month_sums_only_completed_appointments(service, customer, staff_client):
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)
    _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now)

    response = staff_client.get(URL)

    assert response.data["revenue_this_month"] == "500.00"


@pytest.mark.django_db
def test_counts_completed_and_cancelled_this_month(service, customer, staff_client):
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)
    _appointment(
        service, customer, status=AppointmentStatus.CANCELLED, start_datetime=now, cancelled_at=now
    )

    response = staff_client.get(URL)

    assert response.data["completed_appointments_this_month"] == 1
    assert response.data["cancellations_this_month"] == 1
