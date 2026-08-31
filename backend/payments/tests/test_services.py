from datetime import timedelta
from unittest.mock import patch

import pixelpay
import pytest
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from customers.models import Customer
from payments.models import Payment, PaymentStatus
from payments.services import (
    PaymentDeclinedError,
    PaymentError,
    PaymentGatewayError,
    charge_appointment,
    flag_refund_needed,
)

# Response shapes below are copied from real calls made against PixelPay's
# public sandbox (pixelpay.dev) during development -- not guessed.

VALID_CARD = {
    "number": "4111111111111111",
    "cvv": "123",
    "expire_month": 12,
    "expire_year": 2027,
    "cardholder": "Test Customer",
}

VALID_BILLING = {
    "address": "Col. Test 123",
    "country": "HN",
    "state": "HN-CR",
    "city": "Tegucigalpa",
    "zip": "11101",
    "phone": "99999999",
}


def _success_response(payment_uuid="S-a2a1761f-a024-49e4-90a8-965101ca8f63"):
    response = pixelpay.responses.SuccessResponse()
    response.success = True
    response.message = "Pago realizado exitosamente"
    response.errors = None
    response.data = {
        "transaction_type": "sale",
        "response_approved": True,
        "response_code": "00",
        "response_reason": "Transacción completada exitosamente",
        "payment_uuid": payment_uuid,
        "payment_hash": "7d86ec1ca83ad4cc51daf396ad103d88",
    }
    return response


def _declined_response():
    response = pixelpay.responses.PaymentDeclinedResponse()
    response.success = False
    response.message = "Transacción denegada"
    response.errors = None
    response.data = {
        "transaction_type": "sale",
        "response_approved": False,
        "response_code": "05",
        "response_reason": "El banco emisor de la tarjeta no esta dispuesto a aceptar la transacción.",
        "payment_uuid": "S-a2a17868-1a1a-4932-88e5-1d6e80fce23a",
        "payment_hash": None,
    }
    return response


def _input_error_response():
    response = pixelpay.responses.InputErrorResponse()
    response.success = False
    response.message = "El campo email no corresponde con una dirección de e-mail válida."
    response.errors = {"customer_email": ["El campo email no corresponde con una dirección de e-mail válida."]}
    response.data = None
    return response


def _gateway_error_response():
    response = pixelpay.responses.NoAccessResponse()
    response.success = False
    response.message = "Credenciales inválidas."
    response.errors = None
    response.data = None
    return response


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


@pytest.mark.django_db
def test_charge_appointment_confirms_on_approval(appointment):
    with patch(
        "payments.services.pixelpay.services.Transaction.doSale", return_value=_success_response()
    ):
        payment = charge_appointment(appointment, card=VALID_CARD, billing=VALID_BILLING)

    appointment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.pixelpay_payment_uuid == "S-a2a1761f-a024-49e4-90a8-965101ca8f63"
    assert payment.paid_at is not None
    assert payment.amount == appointment.price_snapshot
    assert appointment.status == AppointmentStatus.CONFIRMED


@pytest.mark.django_db
def test_charge_appointment_raises_on_decline(appointment):
    with patch(
        "payments.services.pixelpay.services.Transaction.doSale", return_value=_declined_response()
    ):
        with pytest.raises(PaymentDeclinedError):
            charge_appointment(appointment, card=VALID_CARD, billing=VALID_BILLING)

    appointment.refresh_from_db()
    assert appointment.status == AppointmentStatus.PENDING
    # The whole attempt rolls back with the exception (raised inside the
    # same atomic() block used to lock against a concurrent double
    # charge), so no Payment row is left behind -- a retry starts clean.
    assert not Payment.objects.filter(appointment=appointment).exists()


@pytest.mark.django_db
def test_charge_appointment_raises_declined_error_with_field_errors_on_bad_input(appointment):
    with patch(
        "payments.services.pixelpay.services.Transaction.doSale", return_value=_input_error_response()
    ):
        with pytest.raises(PaymentDeclinedError) as exc_info:
            charge_appointment(appointment, card=VALID_CARD, billing=VALID_BILLING)

    assert exc_info.value.errors == {
        "customer_email": ["El campo email no corresponde con una dirección de e-mail válida."]
    }


@pytest.mark.django_db
def test_charge_appointment_raises_gateway_error_on_unexpected_response(appointment):
    with patch(
        "payments.services.pixelpay.services.Transaction.doSale", return_value=_gateway_error_response()
    ):
        with pytest.raises(PaymentGatewayError):
            charge_appointment(appointment, card=VALID_CARD, billing=VALID_BILLING)


@pytest.mark.django_db
def test_charge_appointment_rejects_non_pending_appointment(appointment):
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.save()

    with pytest.raises(PaymentError):
        charge_appointment(appointment, card=VALID_CARD, billing=VALID_BILLING)


@pytest.mark.django_db
def test_charge_appointment_rejects_already_paid_appointment(appointment):
    Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
    )

    with pytest.raises(PaymentError):
        charge_appointment(appointment, card=VALID_CARD, billing=VALID_BILLING)


@pytest.mark.django_db
def test_flag_refund_needed_is_noop_without_a_payment(appointment):
    flag_refund_needed(appointment)  # must not raise


@pytest.mark.django_db
def test_flag_refund_needed_marks_a_succeeded_payment_refund_pending(appointment):
    payment = Payment.objects.create(
        appointment=appointment,
        amount=appointment.price_snapshot,
        currency="HNL",
        status=PaymentStatus.SUCCEEDED,
    )

    flag_refund_needed(appointment)

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.REFUND_PENDING


@pytest.mark.django_db
def test_flag_refund_needed_leaves_a_non_succeeded_payment_alone(appointment):
    payment = Payment.objects.create(
        appointment=appointment, amount=appointment.price_snapshot, currency="HNL"
    )

    flag_refund_needed(appointment)

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
