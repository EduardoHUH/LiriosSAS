"""The availability engine: the backend's single source of truth for which
appointment start times are actually bookable. Nothing here trusts the
frontend -- this module is re-run on every availability query and (in
appointments/services.py) re-checked again immediately before a booking is
committed.
"""

from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from appointments.models import (
    BLOCKING_APPOINTMENT_STATUSES,
    Appointment,
    UNPAID_HOLD_STATUSES,
)
from core.models import BusinessSettings
from scheduling.models import BlockedTime, BusinessHours, SpecialDate

# Candidate start times are generated on a fixed grid rather than packed
# back-to-back from each service's own duration. This keeps the times shown
# to customers predictable across services of different lengths, and -- just
# as importantly -- gives booking creation a fixed, known set of
# legitimate start times to check a submitted slot against, rather than
# having to re-derive "was this ever actually offered?" from scratch.
SLOT_GRANULARITY_MINUTES = 15

# Statuses that block a slot unconditionally (no unpaid-hold grace window
# to consider), i.e. everything blocking except the hold-expiry-sensitive
# PENDING/AWAITING_PAYMENT states.
_UNCONDITIONALLY_BLOCKING_STATUSES = [
    s for s in BLOCKING_APPOINTMENT_STATUSES if s not in UNPAID_HOLD_STATUSES
]


def _effective_buffer(service):
    if service.buffer_minutes is not None:
        return service.buffer_minutes
    return BusinessSettings.load().default_buffer_minutes


def _open_intervals_for_date(local_date):
    """Returns (start, end) naive-local-time tuples of open time for a date,
    accounting for a SpecialDate override (closed, or custom hours) before
    falling back to the regular weekday BusinessHours."""

    special = SpecialDate.objects.filter(date=local_date).first()
    if special is not None:
        if special.is_closed:
            return []
        return [(special.special_open_time, special.special_close_time)]

    weekday = local_date.weekday()
    hours = BusinessHours.objects.filter(weekday=weekday, is_active=True).order_by(
        "start_time"
    )
    return [(h.start_time, h.end_time) for h in hours]


def _to_aware(local_date, local_time):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(local_date, local_time), tz)


def _day_bounds(local_date):
    return _to_aware(local_date, time.min), _to_aware(local_date, time.max)


def _blocked_ranges_for_date(local_date):
    day_start, day_end = _day_bounds(local_date)
    blocks = BlockedTime.objects.filter(
        start_datetime__lt=day_end, end_datetime__gt=day_start
    )
    return [
        (max(b.start_datetime, day_start), min(b.end_datetime, day_end)) for b in blocks
    ]


def _busy_appointment_ranges_for_date(local_date, buffer_minutes):
    day_start, day_end = _day_bounds(local_date)
    hold_cutoff = timezone.now() - timedelta(
        minutes=BusinessSettings.load().unpaid_hold_minutes
    )

    appointments = Appointment.objects.filter(
        Q(status__in=_UNCONDITIONALLY_BLOCKING_STATUSES)
        | Q(status__in=UNPAID_HOLD_STATUSES, created_at__gte=hold_cutoff),
        start_datetime__lt=day_end,
        end_datetime__gt=day_start,
    )
    buffer = timedelta(minutes=buffer_minutes)
    return [(a.start_datetime, a.end_datetime + buffer) for a in appointments]


def _subtract_ranges(intervals, exclusions):
    if not exclusions:
        return intervals
    exclusions = sorted(exclusions)
    result = []
    for start, end in intervals:
        current = start
        for ex_start, ex_end in exclusions:
            if ex_end <= current or ex_start >= end:
                continue
            if ex_start > current:
                result.append((current, min(ex_start, end)))
            current = max(current, ex_end)
            if current >= end:
                break
        if current < end:
            result.append((current, end))
    return result


def get_available_slots(service, local_date):
    """Returns a sorted list of timezone-aware datetimes on local_date at
    which `service` can be booked, given business hours, holidays/special
    dates, blocked time, existing appointments (with buffer), the global
    accepting-bookings switch, and the min-notice/max-window rules."""

    settings_obj = BusinessSettings.load()
    if not settings_obj.is_accepting_bookings:
        return []
    if not service.is_active or not service.is_bookable:
        return []

    now = timezone.now()
    earliest_allowed = now + timedelta(hours=settings_obj.min_booking_notice_hours)
    today_local = timezone.localtime(now).date()
    latest_allowed_date = today_local + timedelta(days=settings_obj.max_booking_window_days)
    if local_date > latest_allowed_date:
        return []

    open_intervals = [
        (_to_aware(local_date, start), _to_aware(local_date, end))
        for start, end in _open_intervals_for_date(local_date)
    ]
    if not open_intervals:
        return []

    buffer_minutes = _effective_buffer(service)
    exclusions = _blocked_ranges_for_date(local_date) + _busy_appointment_ranges_for_date(
        local_date, buffer_minutes
    )
    free_intervals = _subtract_ranges(open_intervals, exclusions)

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=SLOT_GRANULARITY_MINUTES)

    slots = []
    for interval_start, interval_end in free_intervals:
        candidate = interval_start
        while candidate + duration <= interval_end:
            if candidate >= earliest_allowed:
                slots.append(candidate)
            candidate += step
    slots.sort()
    return slots


def is_slot_available(service, start_datetime):
    """Re-validates one specific candidate slot against the same rules used
    to advertise availability. Used at booking-creation time so a client
    can't request a start time that was never actually offered."""

    local_date = timezone.localtime(start_datetime).date()
    return start_datetime in get_available_slots(service, local_date)
