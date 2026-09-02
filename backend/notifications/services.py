"""Sends transactional emails and logs every attempt to Notification,
whether it succeeds or fails. A broken email provider must never break
the underlying business operation -- every call site here runs *after*
the appointment/auth change it's reporting on has already been
committed, so a send failure only means the customer doesn't get an
email, not that the operation itself is rolled back or reported as
failed to them."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from core.models import BusinessSettings
from notifications.models import Notification, NotificationStatus, NotificationType

logger = logging.getLogger(__name__)


def _send_and_log(*, notification_type, recipient_email, template_name, context, appointment=None):
    if not recipient_email:
        return

    notification = Notification.objects.create(
        appointment=appointment,
        notification_type=notification_type,
        recipient_email=recipient_email,
    )

    try:
        subject = render_to_string(
            f"notifications/emails/{template_name}_subject.txt", context
        ).strip()
        body = render_to_string(f"notifications/emails/{template_name}_body.txt", context).strip()
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient_email])
    except Exception as exc:
        logger.exception("Failed to send %s email to %s", notification_type, recipient_email)
        notification.status = NotificationStatus.FAILED
        notification.error_message = str(exc)
        notification.save()
        return

    notification.status = NotificationStatus.SENT
    notification.sent_at = timezone.now()
    notification.save()


def _appointment_context(appointment):
    return {
        "appointment": appointment,
        "customer": appointment.customer,
        "service": appointment.service,
        "business_name": BusinessSettings.load().business_name,
        "start_local": timezone.localtime(appointment.start_datetime),
        "manage_url": f"{settings.FRONTEND_URL}/citas/{appointment.access_token}",
    }


def send_booking_received_email(appointment):
    """A new booking was created (status pending) -- tells the customer
    their slot is held and that staff will confirm it."""

    _send_and_log(
        notification_type=NotificationType.BOOKING_CONFIRMATION,
        recipient_email=appointment.customer.email,
        template_name="booking_received",
        context=_appointment_context(appointment),
        appointment=appointment,
    )


def send_booking_confirmed_email(appointment):
    """Staff manually confirmed a booking (walk-in, phone, or online request)."""

    _send_and_log(
        notification_type=NotificationType.BOOKING_CONFIRMATION,
        recipient_email=appointment.customer.email,
        template_name="booking_confirmed",
        context=_appointment_context(appointment),
        appointment=appointment,
    )


def send_cancellation_email(appointment):
    _send_and_log(
        notification_type=NotificationType.CANCELLATION,
        recipient_email=appointment.customer.email,
        template_name="cancellation",
        context=_appointment_context(appointment),
        appointment=appointment,
    )


def send_reschedule_email(appointment):
    _send_and_log(
        notification_type=NotificationType.RESCHEDULE,
        recipient_email=appointment.customer.email,
        template_name="reschedule",
        context=_appointment_context(appointment),
        appointment=appointment,
    )


def send_reminder_email(appointment):
    _send_and_log(
        notification_type=NotificationType.REMINDER,
        recipient_email=appointment.customer.email,
        template_name="reminder",
        context=_appointment_context(appointment),
        appointment=appointment,
    )


def send_admin_new_booking_alert(appointment):
    """Internal alert to the salon's own contact address. A no-op if none
    is configured -- BusinessSettings.contact_email is optional."""

    admin_email = BusinessSettings.load().contact_email
    if not admin_email:
        return
    _send_and_log(
        notification_type=NotificationType.ADMIN_ALERT,
        recipient_email=admin_email,
        template_name="admin_new_booking",
        context=_appointment_context(appointment),
        appointment=appointment,
    )


def send_password_reset_email(user, reset_url):
    _send_and_log(
        notification_type=NotificationType.PASSWORD_RESET,
        recipient_email=user.email,
        template_name="password_reset",
        context={
            "user": user,
            "reset_url": reset_url,
            "business_name": BusinessSettings.load().business_name,
        },
    )
