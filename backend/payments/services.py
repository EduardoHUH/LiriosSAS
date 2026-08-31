"""Stripe integration: starting a checkout attempt, applying verified
webhook events, and refunding on cancellation. Views must go through these
functions rather than calling the Stripe SDK directly, so every payment
state change is validated, idempotent, and recorded the same way."""

import logging
from decimal import ROUND_HALF_UP, Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from appointments.models import AppointmentStatus
from appointments.services import transition_appointment
from payments.models import Payment, PaymentStatus, StripeEvent

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Raised when a checkout session or refund cannot be created for the
    current state of an appointment/payment."""


def _to_stripe_amount(amount):
    # Stripe wants the smallest currency unit as an integer, never a float.
    # Coerced through str() -> Decimal rather than trusting the caller
    # already passed a Decimal (a DecimalField assigned a raw string, e.g.
    # from an un-refreshed in-memory instance, stays a str in Python).
    return int((Decimal(str(amount)) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def create_checkout_session(appointment):
    """Starts an online-payment attempt for a pending appointment. Paying
    online is optional: a customer may instead leave the appointment
    pending for staff to confirm without payment (e.g. pay in person).
    Returns the Stripe-hosted checkout URL to redirect the customer to."""

    if appointment.status != AppointmentStatus.PENDING:
        raise PaymentError("Esta cita no está pendiente de pago.")

    payment, _ = Payment.objects.get_or_create(
        appointment=appointment,
        defaults={"amount": appointment.price_snapshot, "currency": "HNL"},
    )
    if payment.status == PaymentStatus.SUCCEEDED:
        raise PaymentError("Esta cita ya fue pagada.")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        customer_email=appointment.customer.email,
        line_items=[
            {
                "price_data": {
                    "currency": payment.currency.lower(),
                    "product_data": {"name": appointment.service.name},
                    "unit_amount": _to_stripe_amount(payment.amount),
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.FRONTEND_URL}/citas/{appointment.access_token}?pago=exitoso",
        cancel_url=f"{settings.FRONTEND_URL}/citas/{appointment.access_token}?pago=cancelado",
        metadata={"appointment_id": str(appointment.id), "payment_id": str(payment.id)},
    )

    payment.stripe_checkout_session_id = session.id
    payment.status = PaymentStatus.PENDING
    payment.save()
    transition_appointment(appointment, AppointmentStatus.AWAITING_PAYMENT)

    return session.url


def construct_event(payload, sig_header):
    """Verifies a webhook request actually came from Stripe and returns the
    event as a plain (JSON-serializable) dict. Raises ValueError or
    stripe.SignatureVerificationError on a bad payload/signature -- the
    webhook view treats both as an invalid request."""

    event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    return event.to_dict()


def process_event(event):
    """Applies one verified Stripe event. Idempotent: a replayed delivery
    of the same event (Stripe retries on a non-2xx response, or can send a
    duplicate) is a no-op after the first, tracked via
    StripeEvent.stripe_event_id."""

    with transaction.atomic():
        _, created = StripeEvent.objects.get_or_create(
            stripe_event_id=event["id"],
            defaults={"event_type": event["type"], "payload": event["data"]},
        )
        if not created:
            return

        if event["type"] == "checkout.session.completed":
            _handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "checkout.session.expired":
            _handle_checkout_expired(event["data"]["object"])


def _handle_checkout_completed(session):
    try:
        payment = Payment.objects.select_related("appointment").get(
            stripe_checkout_session_id=session["id"]
        )
    except Payment.DoesNotExist:
        return

    payment.status = PaymentStatus.SUCCEEDED
    payment.stripe_payment_intent_id = session.get("payment_intent") or ""
    payment.paid_at = timezone.now()
    payment.save()
    transition_appointment(payment.appointment, AppointmentStatus.CONFIRMED)


def _handle_checkout_expired(session):
    # The unpaid-hold grace window (BusinessSettings.unpaid_hold_minutes)
    # already stops an expired hold from blocking availability -- this just
    # keeps the Payment record honest for admin visibility.
    Payment.objects.filter(
        stripe_checkout_session_id=session["id"], status=PaymentStatus.PENDING
    ).update(status=PaymentStatus.FAILED)


def refund_payment(payment):
    if payment.status != PaymentStatus.SUCCEEDED:
        raise PaymentError("Solo se pueden reembolsar pagos exitosos.")

    stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)

    payment.status = PaymentStatus.REFUNDED
    payment.refunded_amount = payment.amount
    payment.save()


def refund_if_paid(appointment):
    """Called after a cancellation has already been approved and committed.
    Unconditional at that point: for a customer, cancel_appointment() only
    lets the cancellation succeed inside the allowed window in the first
    place; for staff, cancelling a paid booking is the salon's own
    decision. A Stripe-side failure here is logged rather than raised --
    the cancellation itself must not be undone or reported as failed to the
    caller just because the refund call didn't go through; staff can retry
    the refund manually from the Stripe dashboard using paid_at/amount."""

    payment = getattr(appointment, "payment", None)
    if payment is None or payment.status != PaymentStatus.SUCCEEDED:
        return
    try:
        refund_payment(payment)
    except stripe.StripeError:
        logger.exception("Stripe refund failed for appointment %s", appointment.id)
