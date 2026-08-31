from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from core.models import BusinessSettings
from notifications.models import Notification, NotificationStatus, NotificationType
from notifications.services import send_reminder_email


class Command(BaseCommand):
    help = (
        "Sends a reminder email for each confirmed appointment whose reminder "
        "window (BusinessSettings.reminder_hours_before) has arrived and that "
        "hasn't already received one. Safe to run as often as needed -- an "
        "appointment already reminded is skipped regardless of how often this "
        "runs. Meant to be triggered periodically by an external scheduler "
        "(e.g. a Railway cron job); nothing in this project runs it on its "
        "own."
    )

    def handle(self, *args, **options):
        now = timezone.now()
        reminder_hours = BusinessSettings.load().reminder_hours_before
        due_by = now + timedelta(hours=reminder_hours)

        # Only excludes a previously SENT reminder, not a FAILED one, so a
        # transient email failure gets retried on the command's next run
        # rather than silently skipping that appointment forever.
        already_reminded = Notification.objects.filter(
            notification_type=NotificationType.REMINDER,
            status=NotificationStatus.SENT,
        ).values_list("appointment_id", flat=True)

        appointments = Appointment.objects.filter(
            status=AppointmentStatus.CONFIRMED,
            start_datetime__gt=now,
            start_datetime__lte=due_by,
        ).exclude(id__in=already_reminded)

        count = 0
        for appointment in appointments:
            send_reminder_email(appointment)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Enviados {count} recordatorio(s)."))
