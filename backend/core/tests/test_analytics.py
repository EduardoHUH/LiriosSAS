from datetime import datetime, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer

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
def test_revenue_trend_buckets_completed_appointments_by_day(service, customer, staff_client):
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)
    _appointment(service, customer, status=AppointmentStatus.CONFIRMED, start_datetime=now)

    response = staff_client.get(REVENUE_URL)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["revenue"] == "500.00"


@pytest.mark.django_db
def test_revenue_trend_buckets_completed_appointments_by_week(service, customer, staff_client):
    # The service function buckets by the *local* (Honduras) date of
    # start_datetime, so the expected period must be derived the same way
    # here -- deriving it from the raw UTC `now` instead could put the
    # test on the wrong side of a weekday boundary during the ~6-hour
    # window where UTC and local dates disagree.
    now = timezone.now()
    today_local = timezone.localtime(now).date()
    monday_local = today_local - timedelta(days=today_local.weekday())
    monday = timezone.make_aware(datetime.combine(monday_local, time(12, 0)))

    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=monday)
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)

    response = staff_client.get(REVENUE_URL, {"group_by": "week"})

    assert response.status_code == 200
    # Both appointments fall in the same local ISO week, so they collapse
    # into one bucket.
    assert len(response.data) == 1
    assert response.data[0]["period"] == monday_local.isoformat()
    assert response.data[0]["revenue"] == "1000.00"


@pytest.mark.django_db
def test_revenue_trend_buckets_completed_appointments_by_month(service, customer, staff_client):
    now = timezone.now()
    first_of_month_local = timezone.localtime(now).date().replace(day=1)
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)

    response = staff_client.get(REVENUE_URL, {"group_by": "month"})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["period"] == first_of_month_local.isoformat()
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
def test_service_popularity_rejects_bad_date_format(staff_client):
    response = staff_client.get(SERVICES_URL, {"date_from": "not-a-date"})

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
def test_service_popularity_and_revenue_trend_agree_on_revenue(service, customer, staff_client):
    """Both endpoints define revenue the same way now (Sum(price_snapshot)
    on COMPLETED appointments) -- this locks that invariant in so a future
    change to one definition without the other doesn't silently drift."""
    now = timezone.now()
    _appointment(service, customer, status=AppointmentStatus.COMPLETED, start_datetime=now)

    services_response = staff_client.get(SERVICES_URL)
    revenue_response = staff_client.get(REVENUE_URL)

    assert services_response.data[0]["appointment_count"] == 1
    assert services_response.data[0]["revenue"] == "500.00"
    assert revenue_response.data[0]["revenue"] == "500.00"
