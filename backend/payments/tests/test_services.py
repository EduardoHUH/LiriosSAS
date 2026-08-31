from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import stripe
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from payments.models import Payment, PaymentStatus, StripeEvent
from payments.services import (
    PaymentError,
    create_checkout_session,
    process_event,
    refund_if_paid,
    refund_payment,
)


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
def appointment(service, customer):
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


def _fake_session(session_id="cs_test_123"):
    return SimpleNamespace(id=session_id, url=f"https://checkout.stripe.com/pay/{session_id}")


@pytest.mark.django_db
def test_create_checkout_session_starts_awaiting_payment(appointment):
    with patch("payments.services.stripe.checkout.Session.create", return_value=_fake_session()):
        url = create_checkout_session(appointment)

    appointment.refresh_from_db()
    payment = Payment.objects.get(appointment=appointment)
    assert url == "https://checkout.stripe.com/pay/cs_test_123"
    assert payment.stripe_checkout_session_id == "cs_test_123"
    assert payment.amount == appointment.price_snapshot
    assert appointment.status == AppointmentStatus.AWAITING_PAYMENT


@pytest.mark.django_db
def test_create_checkout_session_rejects_non_pending_appointment(appointment):
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.save()

    with pytest.raises(PaymentError):
        create_checkout_session(appointment)


@pytest.mark.django_db
def test_create_checkout_session_rejects_already_paid_appointment(appointment):
    Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
    )

    with pytest.raises(PaymentError):
        create_checkout_session(appointment)


@pytest.mark.django_db
def test_process_event_checkout_completed_confirms_appointment(appointment):
    appointment.status = AppointmentStatus.AWAITING_PAYMENT
    appointment.save()
    payment = Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        stripe_checkout_session_id="cs_test_123",
    )
    event = {
        "id": "evt_test_1",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_123", "payment_intent": "pi_test_1"}},
    }

    process_event(event)

    payment.refresh_from_db()
    appointment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.stripe_payment_intent_id == "pi_test_1"
    assert payment.paid_at is not None
    assert appointment.status == AppointmentStatus.CONFIRMED


@pytest.mark.django_db
def test_process_event_is_idempotent(appointment):
    appointment.status = AppointmentStatus.AWAITING_PAYMENT
    appointment.save()
    Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        stripe_checkout_session_id="cs_test_123",
    )
    event = {
        "id": "evt_test_1",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_123", "payment_intent": "pi_test_1"}},
    }

    process_event(event)
    process_event(event)

    assert StripeEvent.objects.filter(stripe_event_id="evt_test_1").count() == 1


@pytest.mark.django_db
def test_process_event_ignores_unknown_checkout_session():
    event = {
        "id": "evt_test_2",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_does_not_exist", "payment_intent": "pi_test_2"}},
    }

    process_event(event)  # must not raise

    assert StripeEvent.objects.filter(stripe_event_id="evt_test_2").exists()


@pytest.mark.django_db
def test_process_event_checkout_expired_marks_payment_failed(appointment):
    payment = Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        stripe_checkout_session_id="cs_test_123",
    )
    event = {
        "id": "evt_test_3",
        "type": "checkout.session.expired",
        "data": {"object": {"id": "cs_test_123"}},
    }

    process_event(event)

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.FAILED


@pytest.mark.django_db
def test_refund_payment_marks_refunded(appointment):
    payment = Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
        stripe_payment_intent_id="pi_test_1",
    )

    with patch("payments.services.stripe.Refund.create") as mock_refund:
        refund_payment(payment)

    mock_refund.assert_called_once_with(payment_intent="pi_test_1")
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.REFUNDED
    assert payment.refunded_amount == payment.amount


@pytest.mark.django_db
def test_refund_payment_rejects_non_succeeded_payment(appointment):
    payment = Payment.objects.create(
        appointment=appointment, amount=appointment.price_snapshot, currency="HNL"
    )

    with pytest.raises(PaymentError):
        refund_payment(payment)


@pytest.mark.django_db
def test_refund_if_paid_is_noop_without_a_payment(appointment):
    refund_if_paid(appointment)  # must not raise


@pytest.mark.django_db
def test_refund_if_paid_refunds_a_succeeded_payment(appointment):
    Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
        stripe_payment_intent_id="pi_test_1",
    )

    with patch("payments.services.stripe.Refund.create") as mock_refund:
        refund_if_paid(appointment)

    mock_refund.assert_called_once_with(payment_intent="pi_test_1")


@pytest.mark.django_db
def test_refund_if_paid_swallows_stripe_errors(appointment):
    payment = Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
        stripe_payment_intent_id="pi_test_1",
    )

    with patch("payments.services.stripe.Refund.create", side_effect=stripe.StripeError("boom")):
        refund_if_paid(appointment)  # must not raise

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
