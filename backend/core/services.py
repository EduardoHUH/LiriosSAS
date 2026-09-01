"""Aggregate read-only data for the admin dashboard overview. Kept
separate from the view so the aggregation logic is testable without HTTP."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
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


def get_revenue_trend(date_from, date_to, group_by="day"):
    """Buckets SUCCEEDED payments by paid_at into day/week/month periods,
    local-timezone-aware. Same payment-based definition of "revenue" as
    get_dashboard_overview's revenue_this_month -- not appointment price,
    so this number and get_service_popularity's revenue are deliberately
    not the same metric (see that function's docstring).

    Bucketing happens in Python rather than via Trunc(tzinfo=...) --
    MySQL's CONVERT_TZ requires the server's time zone tables to be
    loaded (mysql_tzinfo_to_sql), which isn't guaranteed across dev/CI/
    prod environments here. Ranges this query covers (weeks/months of
    payments, not years) are small enough that this isn't a real
    performance concern."""
    range_start, _ = _local_day_bounds(date_from)
    _, range_end = _local_day_bounds(date_to)

    payments = Payment.objects.filter(
        status=PaymentStatus.SUCCEEDED, paid_at__gte=range_start, paid_at__lte=range_end
    ).only("amount", "paid_at")

    buckets = {}
    for payment in payments:
        local_date = timezone.localtime(payment.paid_at).date()
        if group_by == "week":
            period = local_date - timedelta(days=local_date.weekday())
        elif group_by == "month":
            period = local_date.replace(day=1)
        else:
            period = local_date
        buckets[period] = buckets.get(period, Decimal("0.00")) + payment.amount

    return [{"period": period, "revenue": revenue} for period, revenue in sorted(buckets.items())]


def get_service_popularity(date_from, date_to):
    """Groups COMPLETED appointments by service. revenue here is
    Sum(price_snapshot) -- the appointment's booked price -- NOT confirmed
    online payment like get_revenue_trend. A walk-in who pays in person at
    the salon still completed a real appointment; excluding those would
    make "which services are popular" meaningless for services people
    often pay for in person. Do not assume this equals revenue trend."""
    range_start, _ = _local_day_bounds(date_from)
    _, range_end = _local_day_bounds(date_to)

    rows = (
        Appointment.objects.filter(
            status=AppointmentStatus.COMPLETED,
            start_datetime__gte=range_start,
            start_datetime__lte=range_end,
        )
        .values("service__name")
        .annotate(appointment_count=Count("id"), revenue=Sum("price_snapshot"))
        .order_by("-appointment_count")
    )
    return [
        {
            "service_name": row["service__name"],
            "appointment_count": row["appointment_count"],
            "revenue": row["revenue"] or Decimal("0.00"),
        }
        for row in rows
    ]
