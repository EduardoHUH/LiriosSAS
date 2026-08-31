from datetime import datetime, timedelta, timezone

import pytest
from django.db import IntegrityError

from appointments.models import Appointment
from catalog.models import Service, ServiceCategory
from customers.models import Customer


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        full_name="Ana López", email="ana@example.com", phone="99999999"
    )


@pytest.fixture
def service(db):
    category = ServiceCategory.objects.create(name="Maquillaje Test")
    return Service.objects.create(
        category=category,
        name="Maquillaje de novia",
        price="1200.00",
        duration_minutes=90,
    )


@pytest.mark.django_db
def test_end_datetime_must_be_after_start_datetime(customer, service):
    start = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
    end = start - timedelta(minutes=30)

    with pytest.raises(IntegrityError):
        Appointment.objects.create(
            customer=customer,
            service=service,
            start_datetime=start,
            end_datetime=end,
            price_snapshot=service.price,
            duration_minutes_snapshot=service.duration_minutes,
        )


@pytest.mark.django_db
def test_access_token_is_generated_automatically_and_unique(customer, service):
    start = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)

    first = Appointment.objects.create(
        customer=customer,
        service=service,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=service.duration_minutes),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )
    second = Appointment.objects.create(
        customer=customer,
        service=service,
        start_datetime=start + timedelta(days=1),
        end_datetime=start + timedelta(days=1, minutes=service.duration_minutes),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    assert first.access_token
    assert first.access_token != second.access_token
