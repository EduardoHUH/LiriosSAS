import hashlib
import hmac
import json
import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import stripe
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from payments.models import Payment, PaymentStatus

User = get_user_model()

WEBHOOK_SECRET = "whsec_test_secret"


def _stripe_signature(payload: bytes, secret: str = WEBHOOK_SECRET) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


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
def test_pay_action_returns_checkout_url(pending_appointment):
    client = APIClient()
    fake_session = SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.com/pay/cs_test_123")

    with patch("payments.services.stripe.checkout.Session.create", return_value=fake_session):
        response = client.post(f"/api/v1/appointments/{pending_appointment.access_token}/pay/")

    assert response.status_code == 200, response.data
    assert response.data["checkout_url"] == fake_session.url
    pending_appointment.refresh_from_db()
    assert pending_appointment.status == AppointmentStatus.AWAITING_PAYMENT


@pytest.mark.django_db
def test_pay_action_returns_502_on_stripe_outage(pending_appointment):
    client = APIClient()

    with patch(
        "payments.services.stripe.checkout.Session.create",
        side_effect=stripe.AuthenticationError("no api key provided"),
    ):
        response = client.post(f"/api/v1/appointments/{pending_appointment.access_token}/pay/")

    assert response.status_code == 502
    pending_appointment.refresh_from_db()
    assert pending_appointment.status == AppointmentStatus.PENDING


@pytest.mark.django_db
def test_pay_action_rejects_already_confirmed_appointment(confirmed_appointment):
    client = APIClient()

    response = client.post(f"/api/v1/appointments/{confirmed_appointment.access_token}/pay/")

    assert response.status_code == 400


@pytest.mark.django_db
@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_webhook_rejects_invalid_signature():
    client = APIClient()
    payload = json.dumps({"id": "evt_1", "type": "checkout.session.completed"}).encode()

    response = client.post(
        "/api/v1/payments/webhook/",
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=123,v1=not-a-real-signature",
    )

    assert response.status_code == 400


@pytest.mark.django_db
@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_webhook_confirms_appointment_on_checkout_completed(pending_appointment):
    payment = Payment.objects.create(
        appointment=pending_appointment,
        amount=pending_appointment.price_snapshot,
        currency="HNL",
        stripe_checkout_session_id="cs_test_123",
    )
    pending_appointment.status = AppointmentStatus.AWAITING_PAYMENT
    pending_appointment.save()

    payload = json.dumps(
        {
            "id": "evt_webhook_1",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123", "payment_intent": "pi_test_1"}},
        }
    ).encode()
    client = APIClient()

    response = client.post(
        "/api/v1/payments/webhook/",
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_stripe_signature(payload),
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    pending_appointment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert pending_appointment.status == AppointmentStatus.CONFIRMED


@pytest.mark.django_db
def test_customer_cancel_refunds_a_paid_appointment(confirmed_appointment):
    Payment.objects.create(
        appointment=confirmed_appointment,
        amount=confirmed_appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
        stripe_payment_intent_id="pi_test_1",
    )
    client = APIClient()

    with patch("payments.services.stripe.Refund.create") as mock_refund:
        response = client.post(f"/api/v1/appointments/{confirmed_appointment.access_token}/cancel/")

    assert response.status_code == 200, response.data
    mock_refund.assert_called_once_with(payment_intent="pi_test_1")
    payment = Payment.objects.get(appointment=confirmed_appointment)
    assert payment.status == PaymentStatus.REFUNDED


@pytest.mark.django_db
def test_admin_cancel_refunds_a_paid_appointment(staff_client, confirmed_appointment):
    Payment.objects.create(
        appointment=confirmed_appointment,
        amount=confirmed_appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
        stripe_payment_intent_id="pi_test_1",
    )

    with patch("payments.services.stripe.Refund.create") as mock_refund:
        response = staff_client.post(f"/api/v1/admin/appointments/{confirmed_appointment.id}/cancel/")

    assert response.status_code == 200, response.data
    mock_refund.assert_called_once_with(payment_intent="pi_test_1")
