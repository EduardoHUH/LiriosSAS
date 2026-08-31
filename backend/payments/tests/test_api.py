from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from payments.models import Payment, PaymentStatus
from payments.tests.test_services import (
    VALID_BILLING,
    VALID_CARD,
    _declined_response,
    _success_response,
)

User = get_user_model()

CHARGE_PAYLOAD = {
    "card_number": VALID_CARD["number"],
    "card_cvv": VALID_CARD["cvv"],
    "card_expire_month": VALID_CARD["expire_month"],
    "card_expire_year": VALID_CARD["expire_year"],
    "cardholder": VALID_CARD["cardholder"],
    "billing_address": VALID_BILLING["address"],
    "billing_country": VALID_BILLING["country"],
    "billing_state": VALID_BILLING["state"],
    "billing_city": VALID_BILLING["city"],
    "billing_zip": VALID_BILLING["zip"],
    "billing_phone": VALID_BILLING["phone"],
}

DOSALE = "payments.services.pixelpay.services.Transaction.doSale"


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


@pytest.fixture
def pending_appointment(service, customer):
    start = timezone.now() + timedelta(days=1)
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.PENDING,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )


@pytest.fixture
def confirmed_appointment(service, customer):
    # Well clear of the default 24h cancellation deadline so the customer
    # cancel test below isn't flaky against wall-clock timing.
    start = timezone.now() + timedelta(days=3)
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )


@pytest.mark.django_db
def test_pay_action_confirms_appointment_on_approval(pending_appointment):
    client = APIClient()

    with patch(DOSALE, return_value=_success_response()):
        response = client.post(
            f"/api/v1/appointments/{pending_appointment.access_token}/pay/", CHARGE_PAYLOAD
        )

    assert response.status_code == 200, response.data
    assert response.data["status"] == AppointmentStatus.CONFIRMED
    payment = Payment.objects.get(appointment=pending_appointment)
    assert payment.status == PaymentStatus.SUCCEEDED


@pytest.mark.django_db
def test_pay_action_returns_400_on_decline(pending_appointment):
    client = APIClient()

    with patch(DOSALE, return_value=_declined_response()):
        response = client.post(
            f"/api/v1/appointments/{pending_appointment.access_token}/pay/", CHARGE_PAYLOAD
        )

    assert response.status_code == 400
    pending_appointment.refresh_from_db()
    assert pending_appointment.status == AppointmentStatus.PENDING


@pytest.mark.django_db
def test_pay_action_rejects_incomplete_card_data(pending_appointment):
    client = APIClient()

    response = client.post(
        f"/api/v1/appointments/{pending_appointment.access_token}/pay/",
        {"card_number": VALID_CARD["number"]},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_pay_action_rejects_already_confirmed_appointment(confirmed_appointment):
    client = APIClient()

    response = client.post(
        f"/api/v1/appointments/{confirmed_appointment.access_token}/pay/", CHARGE_PAYLOAD
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_customer_cancel_flags_a_paid_appointment_refund_pending(confirmed_appointment):
    Payment.objects.create(
        appointment=confirmed_appointment,
        amount=confirmed_appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
    )
    client = APIClient()

    response = client.post(f"/api/v1/appointments/{confirmed_appointment.access_token}/cancel/")

    assert response.status_code == 200, response.data
    payment = Payment.objects.get(appointment=confirmed_appointment)
    assert payment.status == PaymentStatus.REFUND_PENDING


@pytest.mark.django_db
def test_admin_cancel_flags_a_paid_appointment_refund_pending(staff_client, confirmed_appointment):
    Payment.objects.create(
        appointment=confirmed_appointment,
        amount=confirmed_appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
    )

    response = staff_client.post(f"/api/v1/admin/appointments/{confirmed_appointment.id}/cancel/")

    assert response.status_code == 200, response.data
    payment = Payment.objects.get(appointment=confirmed_appointment)
    assert payment.status == PaymentStatus.REFUND_PENDING
