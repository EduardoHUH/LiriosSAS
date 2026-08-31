"""Aggregate read-only data for the admin dashboard overview. Kept
separate from the view so the aggregation logic is testable without HTTP."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus
from payments.models import Payment, PaymentStatus


def _local_day_bounds(local_date):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(local_date, time.min), tz), timezone.make_aware(
        datetime.combine(local_date, time.max), tz
    )


def get_dashboard_overview():
    now = timezone.now()
    today_local = timezone.localtime(now).date()
    today_start, today_end = _local_day_bounds(today_local)
    month_start, _ = _local_day_bounds(today_local.replace(day=1))
    upcoming_until = now + timedelta(days=7)

    appointments_today = (
        Appointment.objects.filter(start_datetime__gte=today_start, start_datetime__lte=today_end)
        .exclude(status=AppointmentStatus.CANCELLED)
        .count()
    )

    upcoming_appointments_next_7_days = Appointment.objects.filter(
        status=AppointmentStatus.CONFIRMED,
        start_datetime__gt=now,
        start_datetime__lte=upcoming_until,
    ).count()

    revenue_this_month = (
        Payment.objects.filter(status=PaymentStatus.SUCCEEDED, paid_at__gte=month_start).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    completed_appointments_this_month = Appointment.objects.filter(
        status=AppointmentStatus.COMPLETED, start_datetime__gte=month_start
    ).count()

    cancellations_this_month = Appointment.objects.filter(
        status=AppointmentStatus.CANCELLED, cancelled_at__gte=month_start
    ).count()

    pending_payments = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    refund_pending_payments = Payment.objects.filter(status=PaymentStatus.REFUND_PENDING).count()

    return {
        "appointments_today": appointments_today,
        "upcoming_appointments_next_7_days": upcoming_appointments_next_7_days,
        "revenue_this_month": revenue_this_month,
        "completed_appointments_this_month": completed_appointments_this_month,
        "cancellations_this_month": cancellations_this_month,
        "pending_payments": pending_payments,
        "refund_pending_payments": refund_pending_payments,
    }
