from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from reviews.models import Review, ReviewStatus


@pytest.fixture
def category(db):
    return ServiceCategory.objects.create(name="Maquillaje Prueba")


@pytest.fixture
def service(category):
    return Service.objects.create(
        category=category, name="Servicio", price="500.00", duration_minutes=60
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        full_name="Ana López", email="ana@example.com", phone="99999999"
    )


def _make_appointment(service, customer, status):
    now = timezone.now()
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=status,
        start_datetime=now - timedelta(days=1),
        end_datetime=now - timedelta(days=1) + timedelta(minutes=60),
        price_snapshot="500.00",
        duration_minutes_snapshot=60,
    )


@pytest.mark.django_db
def test_review_action_succeeds_for_a_completed_appointment(service, customer):
    appointment = _make_appointment(service, customer, AppointmentStatus.COMPLETED)
    client = APIClient()

    response = client.post(
        f"/api/v1/appointments/{appointment.access_token}/review/",
        {"rating": 5, "comment": "Excelente atención"},
    )

    assert response.status_code == 201, response.data
    assert response.data["review"]["rating"] == 5
    assert response.data["review"]["status"] == ReviewStatus.PENDING
    review = Review.objects.get(appointment=appointment)
    assert review.reviewer_name == "Ana López"


@pytest.mark.django_db
def test_review_action_rejects_a_non_completed_appointment(service, customer):
    appointment = _make_appointment(service, customer, AppointmentStatus.CONFIRMED)
    client = APIClient()

    response = client.post(
        f"/api/v1/appointments/{appointment.access_token}/review/",
        {"rating": 4, "comment": ""},
    )

    assert response.status_code == 400
    assert not Review.objects.filter(appointment=appointment).exists()


@pytest.mark.django_db
def test_review_action_rejects_a_second_review_for_the_same_appointment(service, customer):
    appointment = _make_appointment(service, customer, AppointmentStatus.COMPLETED)
    client = APIClient()
    first = client.post(
        f"/api/v1/appointments/{appointment.access_token}/review/",
        {"rating": 5, "comment": "Primera"},
    )
    assert first.status_code == 201

    second = client.post(
        f"/api/v1/appointments/{appointment.access_token}/review/",
        {"rating": 1, "comment": "Segunda"},
    )

    assert second.status_code == 400
    assert Review.objects.filter(appointment=appointment).count() == 1


@pytest.mark.django_db
def test_appointment_detail_shows_null_review_before_one_is_submitted(service, customer):
    appointment = _make_appointment(service, customer, AppointmentStatus.COMPLETED)
    client = APIClient()

    response = client.get(f"/api/v1/appointments/{appointment.access_token}/")

    assert response.status_code == 200
    assert response.data["review"] is None
