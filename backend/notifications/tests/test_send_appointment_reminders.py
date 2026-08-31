from datetime import timedelta
from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from catalog.models import Service, ServiceCategory
from core.models import BusinessSettings
from customers.models import Customer
from notifications.models import Notification, NotificationStatus, NotificationType


@pytest.fixture
def customer(db):
    return Customer.objects.create(full_name="Ana López", email="ana@example.com", phone="99999999")


@pytest.fixture
def service(db):
    category = ServiceCategory.objects.create(name="Maquillaje Prueba")
    return Service.objects.create(
        category=category, name="Servicio de prueba", price="500.00", duration_minutes=60
    )


def _appointment(service, customer, *, status, start_datetime):
    return Appointment.objects.create(
        customer=customer,
        service=service,
        status=status,
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )


def _run_command():
    out = StringIO()
    call_command("send_appointment_reminders", stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_sends_reminder_for_confirmed_appointment_within_window(service, customer):
    BusinessSettings.load()  # default reminder_hours_before = 24
    appt = _appointment(
        service, customer, status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(hours=12),
    )

    _run_command()

    assert len(mail.outbox) == 1
    notification = Notification.objects.get(appointment=appt)
    assert notification.notification_type == NotificationType.REMINDER
    assert notification.status == NotificationStatus.SENT


@pytest.mark.django_db
def test_skips_appointment_outside_the_window(service, customer):
    _appointment(
        service, customer, status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(days=5),
    )

    _run_command()

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_skips_non_confirmed_appointment(service, customer):
    _appointment(
        service, customer, status=AppointmentStatus.PENDING,
        start_datetime=timezone.now() + timedelta(hours=12),
    )

    _run_command()

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_does_not_resend_an_already_sent_reminder(service, customer):
    appt = _appointment(
        service, customer, status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(hours=12),
    )
    Notification.objects.create(
        appointment=appt,
        notification_type=NotificationType.REMINDER,
        recipient_email=customer.email,
        status=NotificationStatus.SENT,
    )

    _run_command()

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_retries_a_previously_failed_reminder(service, customer):
    appt = _appointment(
        service, customer, status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(hours=12),
    )
    Notification.objects.create(
        appointment=appt,
        notification_type=NotificationType.REMINDER,
        recipient_email=customer.email,
        status=NotificationStatus.FAILED,
    )

    _run_command()

    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_respects_custom_reminder_hours_before(service, customer):
    settings_obj = BusinessSettings.load()
    settings_obj.reminder_hours_before = 2
    settings_obj.save()
    _appointment(
        service, customer, status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(hours=12),
    )

    _run_command()

    assert len(mail.outbox) == 0
