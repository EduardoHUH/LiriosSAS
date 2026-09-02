"""create_review_for_appointment's friendly .exists() pre-check can't fully
close the race window between two near-simultaneous review submissions for
the same appointment -- the OneToOneField's DB-level uniqueness is the real
backstop (see the function's own docstring/comments). This exercises that
backstop directly by forcing the pre-check to pass for both submissions,
same as a real race would, rather than only testing the friendly path the
existing test_review_action.py already covers."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from reviews.models import Review
from reviews.services import ReviewNotAllowedError, create_review_for_appointment


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
def test_duplicate_review_race_is_caught_by_the_db_backstop_not_just_the_precheck(
    completed_appointment,
):
    create_review_for_appointment(completed_appointment, rating=5, comment="Primera")

    # Simulate the race window: a second submission that reaches the
    # .exists() pre-check before the first one has committed would see
    # False here too, same as a real concurrent request. Without the
    # OneToOneField's DB-level uniqueness backstop, this would create a
    # second Review for the same appointment.
    with patch("reviews.services.Review.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = False
        with pytest.raises(ReviewNotAllowedError):
            create_review_for_appointment(completed_appointment, rating=1, comment="Segunda")

    assert Review.objects.filter(appointment=completed_appointment).count() == 1
