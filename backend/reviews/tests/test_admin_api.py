from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from reviews.models import Review, ReviewStatus

User = get_user_model()


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def completed_appointment(db):
    category = ServiceCategory.objects.create(name="Maquillaje Prueba")
    service = Service.objects.create(
        category=category, name="Servicio", price="500.00", duration_minutes=60
    )
    customer = Customer.objects.create(
        full_name="Ana López", email="ana@example.com", phone="99999999"
    )
    now = timezone.now()
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.COMPLETED,
        start_datetime=now - timedelta(days=1),
        end_datetime=now - timedelta(days=1) + timedelta(minutes=60),
        price_snapshot="500.00",
        duration_minutes_snapshot=60,
    )


@pytest.mark.django_db
def test_admin_endpoints_require_authentication():
    client = APIClient()

    response = client.get("/api/v1/admin/reviews/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_reviews_cannot_be_created_directly_via_admin_api(staff_client):
    client, _ = staff_client

    response = client.post("/api/v1/admin/reviews/", {"rating": 5, "comment": "Excelente"})

    assert response.status_code == 405


@pytest.mark.django_db
def test_approve_action_updates_status_and_moderator(staff_client, completed_appointment):
    client, user = staff_client
    review = Review.objects.create(
        appointment=completed_appointment, reviewer_name="Ana López", rating=5, comment="Genial"
    )

    response = client.post("/api/v1/admin/reviews/approve/", {"ids": [review.id]})

    assert response.status_code == 200
    review.refresh_from_db()
    assert review.status == ReviewStatus.APPROVED
    assert review.moderated_by == user
    assert review.moderated_at is not None


@pytest.mark.django_db
def test_reject_action_updates_status_and_moderator(staff_client, completed_appointment):
    client, user = staff_client
    review = Review.objects.create(
        appointment=completed_appointment, reviewer_name="Ana López", rating=1, comment="Malo"
    )

    response = client.post("/api/v1/admin/reviews/reject/", {"ids": [review.id]})

    assert response.status_code == 200
    review.refresh_from_db()
    assert review.status == ReviewStatus.REJECTED
    assert review.moderated_by == user
    assert review.moderated_at is not None


@pytest.mark.django_db
def test_only_approved_reviews_are_public(completed_appointment):
    Review.objects.create(
        appointment=completed_appointment,
        reviewer_name="Ana López",
        rating=5,
        comment="Pendiente",
        status=ReviewStatus.PENDING,
    )
    client = APIClient()

    response = client.get("/api/v1/reviews/")

    assert response.status_code == 200
    assert response.data == []
