from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from payments.models import Payment, PaymentStatus

User = get_user_model()

REVENUE_URL = "/api/v1/admin/analytics/revenue/"
SERVICES_URL = "/api/v1/admin/analytics/services/"


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
def category(db):
    return ServiceCategory.objects.create(name="Maquillaje Prueba")


@pytest.fixture
def service(category):
    return Service.objects.create(
        category=category, name="Servicio A", price="500.00", duration_minutes=60
    )


@pytest.fixture
def other_service(category):
    return Service.objects.create(
        category=category, name="Servicio B", price="300.00", duration_minutes=45
    )


def _appointment(service, customer, *, status, start_datetime):
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=status,
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )


@pytest.mark.django_db
def test_revenue_trend_requires_staff():
    client = APIClient()

    response = client.get(REVENUE_URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_revenue_trend_buckets_succeeded_payments_by_day(service, customer, staff_client):
    now = timezone.now()
    appt = _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now)
    Payment.objects.create(
        appointment=appt, amount="500.00", currency="HNL", status=PaymentStatus.SUCCEEDED, paid_at=now
    )
    other_appt = _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now)
    Payment.objects.create(
        appointment=other_appt, amount="300.00", currency="HNL", status=PaymentStatus.PENDING
    )

    response = staff_client.get(REVENUE_URL)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["revenue"] == "500.00"


@pytest.mark.django_db
def test_revenue_trend_rejects_bad_group_by(staff_client):
    response = staff_client.get(REVENUE_URL, {"group_by": "year"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_revenue_trend_rejects_bad_date_format(staff_client):
    response = staff_client.get(REVENUE_URL, {"date_from": "not-a-date"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_service_popularity_counts_completed_appointments_by_service(
    service, other_service, customer, staff_client
):
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)
    _appointment(other_service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)
    _appointment(service, customer, status=AppointmentStatus.CANCELLED, start_datetime=now)

    response = staff_client.get(SERVICES_URL)

    assert response.status_code == 200
    by_name = {row["service_name"]: row for row in response.data}
    assert by_name["Servicio A"]["appointment_count"] == 2
    assert by_name["Servicio A"]["revenue"] == "1000.00"
    assert by_name["Servicio B"]["appointment_count"] == 1


@pytest.mark.django_db
def test_service_popularity_counts_a_completed_but_unpaid_appointment(service, customer, staff_client):
    """The whole point of using appointment price rather than payment
    status here: a walk-in who pays in person still completed a real
    appointment, so it must count toward popularity even with no Payment
    row at all -- unlike revenue_trend, which would show zero for it."""
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)

    services_response = staff_client.get(SERVICES_URL)
    revenue_response = staff_client.get(REVENUE_URL)

    assert services_response.data[0]["appointment_count"] == 1
    assert services_response.data[0]["revenue"] == "500.00"
    assert revenue_response.data == []
