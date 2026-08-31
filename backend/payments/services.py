"""PixelPay integration: synchronously charging a card for a pending
appointment, and flagging a cancelled paid appointment for a manual
refund. Views must go through these functions rather than calling the
PixelPay SDK directly.

Unlike Stripe, PixelPay's Sale API has no browser-side tokenization
option we could verify -- the official SDK is a server-side package that
submits the raw card number, CVV, and expiry directly in the charge
request. That means those fields necessarily pass through this backend
in memory for the duration of one request. They are never logged or
persisted; only the gateway's own transaction identifier is stored on
Payment.

Refunds are not automated here: voiding/refunding a PixelPay transaction
requires a 128-character (SHA-512-length) void_signature whose derivation
isn't documented anywhere reachable -- their docs site is a JS app that
doesn't render for automated tools, and no formula appears in the
official SDK source. Guessing at a security-relevant hash formula against
a live payment API isn't an acceptable way to resolve that, so a
cancelled paid appointment is flagged refund_pending instead, for the
salon owner to refund manually from the PixelPay merchant dashboard."""

import logging

import pixelpay
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from appointments.services import transition_appointment
from payments.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Raised when a charge can't even be attempted for the current state
    of an appointment/payment -- not a card decline."""


class PaymentDeclinedError(Exception):
    """Raised when PixelPay processed the request but didn't approve it
    (bad card, insufficient funds, or invalid card/billing input). Safe to
    show to the customer and let them retry."""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class PaymentGatewayError(Exception):
    """Raised when PixelPay couldn't be reached, rejected our credentials,
    or returned an unexpected error unrelated to the card itself."""


def _build_settings():
    pp_settings = pixelpay.models.Settings()
    if settings.PIXELPAY_SANDBOX:
        pp_settings.setupSandbox()
    else:
        pp_settings.setupCredentials(settings.PIXELPAY_AUTH_KEY, settings.PIXELPAY_AUTH_HASH)
        pp_settings.setupEndpoint(settings.PIXELPAY_ENDPOINT)
    pp_settings.setupLanguage("es")
    return pp_settings


def charge_appointment(appointment, *, card, billing):
    """Synchronously charges `card` for a pending appointment's full
    price and, on approval, confirms it. `card` and `billing` are plain
    dicts of the raw fields PixelPay's Sale API requires (see
    payments.serializers.CardChargeSerializer) -- held only in local
    variables for the duration of this call, never written to the
    database or logged.

    Holds a row lock on the appointment for the duration of the (network)
    call to PixelPay, deliberately: unlike a Stripe Checkout redirect,
    this is the actual money-moving step, so a concurrent duplicate
    submission (double-click, retried request) must be serialized here
    rather than risking a real double charge.
    """

    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
        if appointment.status != AppointmentStatus.PENDING:
            raise PaymentError("Esta cita no está pendiente de pago.")

        payment, _ = Payment.objects.get_or_create(
            appointment=appointment,
            defaults={"amount": appointment.price_snapshot, "currency": "HNL"},
        )
        if payment.status == PaymentStatus.SUCCEEDED:
            raise PaymentError("Esta cita ya fue pagada.")

        pp_card = pixelpay.models.Card()
        pp_card.number = card["number"]
        pp_card.cvv2 = card["cvv"]
        pp_card.expire_month = card["expire_month"]
        pp_card.expire_year = card["expire_year"]
        pp_card.cardholder = card["cardholder"]

        pp_billing = pixelpay.models.Billing()
        pp_billing.address = billing["address"]
        pp_billing.country = billing["country"]
        pp_billing.state = billing["state"]
        pp_billing.city = billing["city"]
        pp_billing.zip = billing["zip"]
        pp_billing.phone = billing["phone"]

        order = pixelpay.models.Order()
        order.id = f"LIRIOS-{appointment.id}"
        order.currency = payment.currency
        item = pixelpay.models.Item()
        item.sku = str(appointment.service_id)
        item.description = appointment.service.name
        item.price = float(payment.amount)
        item.qty = 1
        order.addItem(item)
        order.customer_name = appointment.customer.full_name
        order.customer_email = appointment.customer.email

        txn = pixelpay.requests.SaleTransaction()
        txn.setCard(pp_card)
        txn.setBilling(pp_billing)
        txn.setOrder(order)

        gateway = pixelpay.services.Transaction(_build_settings())
        response = gateway.doSale(txn)

        if isinstance(response, pixelpay.responses.SuccessResponse):
            data = response.data or {}
            payment.status = PaymentStatus.SUCCEEDED
            payment.pixelpay_payment_uuid = data.get("payment_uuid", "")
            payment.paid_at = timezone.now()
            payment.save()
            transition_appointment(appointment, AppointmentStatus.CONFIRMED)
            return payment

        if isinstance(
            response, (pixelpay.responses.PaymentDeclinedResponse, pixelpay.responses.InputErrorResponse)
        ):
            raise PaymentDeclinedError(response.message or "El pago fue rechazado.", errors=response.errors)

        logger.error(
            "PixelPay gateway error charging appointment %s: %s (%s)",
            appointment.id,
            response.message,
            type(response).__name__,
        )
        raise PaymentGatewayError(response.message or "No se pudo procesar el pago.")


def flag_refund_needed(appointment):
    """Called after a cancellation has already been approved and
    committed. Does not call PixelPay -- see the module docstring for
    why automated refunds aren't wired up yet. Marks the payment so staff
    can see it needs a manual refund (Django admin, or the future admin
    dashboard) and record it as done once completed."""

    payment = getattr(appointment, "payment", None)
    if payment is not None and payment.status == PaymentStatus.SUCCEEDED:
        payment.status = PaymentStatus.REFUND_PENDING
        payment.save()
