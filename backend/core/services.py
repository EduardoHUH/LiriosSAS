"""Aggregate read-only data for the admin dashboard overview. Kept
separate from the view so the aggregation logic is testable without HTTP."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus


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
        Appointment.objects.filter(
            status=AppointmentStatus.COMPLETED, start_datetime__gte=month_start
        ).aggregate(total=Sum("price_snapshot"))["total"]
        or Decimal("0.00")
    )

    completed_appointments_this_month = Appointment.objects.filter(
        status=AppointmentStatus.COMPLETED, start_datetime__gte=month_start
    ).count()

    cancellations_this_month = Appointment.objects.filter(
        status=AppointmentStatus.CANCELLED, cancelled_at__gte=month_start
    ).count()

    return {
        "appointments_today": appointments_today,
        "upcoming_appointments_next_7_days": upcoming_appointments_next_7_days,
        "revenue_this_month": revenue_this_month,
        "completed_appointments_this_month": completed_appointments_this_month,
        "cancellations_this_month": cancellations_this_month,
    }


def get_revenue_trend(date_from, date_to, group_by="day"):
    """Buckets COMPLETED appointments by start_datetime into day/week/month
    periods, local-timezone-aware, summing price_snapshot -- the same
    revenue definition get_service_popularity already uses (see that
    function's docstring), just bucketed over time instead of by service.

    Bucketing happens in Python rather than via Trunc(tzinfo=...) --
    MySQL's CONVERT_TZ requires the server's time zone tables to be
    loaded (mysql_tzinfo_to_sql), which isn't guaranteed across dev/CI/
    prod environments here. Ranges this query covers (weeks/months, not
    years) are small enough that this isn't a real performance concern."""
    range_start, _ = _local_day_bounds(date_from)
    _, range_end = _local_day_bounds(date_to)

    appointments = Appointment.objects.filter(
        status=AppointmentStatus.COMPLETED,
        start_datetime__gte=range_start,
        start_datetime__lte=range_end,
    ).only("price_snapshot", "start_datetime")

    buckets = {}
    for appointment in appointments:
        local_date = timezone.localtime(appointment.start_datetime).date()
        if group_by == "week":
            period = local_date - timedelta(days=local_date.weekday())
        elif group_by == "month":
            period = local_date.replace(day=1)
        else:
            period = local_date
        buckets[period] = buckets.get(period, Decimal("0.00")) + appointment.price_snapshot

    return [{"period": period, "revenue": revenue} for period, revenue in sorted(buckets.items())]


def get_service_popularity(date_from, date_to):
    """Groups COMPLETED appointments by service. revenue here is
    Sum(price_snapshot) -- the appointment's booked price, same definition
    get_revenue_trend uses -- so a walk-in who never pays online still
    counts; there's no other kind of payment to distinguish from."""
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
