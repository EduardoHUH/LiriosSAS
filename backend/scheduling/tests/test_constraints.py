from datetime import datetime, timezone

import pytest
from django.db import IntegrityError

from scheduling.models import BlockedTime, BusinessHours, Weekday


@pytest.mark.django_db
def test_business_hours_end_time_must_be_after_start_time():
    with pytest.raises(IntegrityError):
        BusinessHours.objects.create(
            weekday=Weekday.MONDAY, start_time="13:00", end_time="09:00"
        )


@pytest.mark.django_db
def test_blocked_time_end_must_be_after_start():
    start = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(IntegrityError):
        BlockedTime.objects.create(start_datetime=start, end_datetime=end)
