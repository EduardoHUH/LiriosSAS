from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from core.models import BusinessSettings
from customers.models import Customer
from notifications.models import Notification, NotificationStatus, NotificationType
from notifications.services import (
    send_admin_new_booking_alert,
    send_booking_confirmed_email,
    send_booking_received_email,
    send_cancellation_email,
    send_password_reset_email,
    send_reminder_email,
    send_reschedule_email,
)

User = get_user_model()


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
        status=AppointmentStatus.CONFIRMED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )


@pytest.mark.parametrize(
    "send_fn,expected_type",
    [
        (send_booking_received_email, NotificationType.BOOKING_CONFIRMATION),
        (send_booking_confirmed_email, NotificationType.BOOKING_CONFIRMATION),
        (send_cancellation_email, NotificationType.CANCELLATION),
        (send_reschedule_email, NotificationType.RESCHEDULE),
        (send_reminder_email, NotificationType.REMINDER),
    ],
)
@pytest.mark.django_db
def test_appointment_email_sends_and_logs(appointment, send_fn, expected_type):
    send_fn(appointment)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [appointment.customer.email]
    notification = Notification.objects.get()
    assert notification.notification_type == expected_type
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None
    assert notification.appointment_id == appointment.id


@pytest.mark.django_db
def test_admin_alert_sent_when_contact_email_configured(appointment):
    settings_obj = BusinessSettings.load()
    settings_obj.contact_email = "owner@example.com"
    settings_obj.save()

    send_admin_new_booking_alert(appointment)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["owner@example.com"]
    assert Notification.objects.get().notification_type == NotificationType.ADMIN_ALERT


@pytest.mark.django_db
def test_admin_alert_is_noop_without_contact_email(appointment):
    send_admin_new_booking_alert(appointment)

    assert len(mail.outbox) == 0
    assert not Notification.objects.exists()


@pytest.mark.django_db
def test_password_reset_email_sends_and_logs():
    user = User.objects.create_user(username="admin", email="admin@example.com", password="x")

    send_password_reset_email(user, "http://localhost:5173/reset-password/uid/token/")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["admin@example.com"]
    assert "reset-password/uid/token" in mail.outbox[0].body
    notification = Notification.objects.get()
    assert notification.notification_type == NotificationType.PASSWORD_RESET
    assert notification.appointment is None


@pytest.mark.django_db
def test_failed_send_is_logged_without_raising(appointment):
    with patch("notifications.services.send_mail", side_effect=Exception("smtp down")):
        send_cancellation_email(appointment)  # must not raise

    notification = Notification.objects.get()
    assert notification.status == NotificationStatus.FAILED
    assert notification.error_message == "smtp down"


@pytest.mark.django_db
def test_no_email_sent_or_logged_when_customer_has_no_email(appointment):
    appointment.customer.email = ""
    appointment.customer.save()

    send_cancellation_email(appointment)

    assert len(mail.outbox) == 0
    assert not Notification.objects.exists()
