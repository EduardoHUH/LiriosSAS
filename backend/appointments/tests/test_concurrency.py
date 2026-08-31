"""Booking integrity requires that double-booking is
structurally impossible even when multiple requests race for the same
slot. This uses real threads and real database commits (not the default
single-transaction test isolation) to actually exercise that race, rather
than just asserting the code *looks* like it should be safe."""

import threading
from datetime import datetime, time, timedelta

import pytest
from django.db import connection
from django.utils import timezone

from appointments.models import Appointment
from appointments.services import SlotNotAvailableError, create_appointment
from catalog.models import Service, ServiceCategory
from scheduling.models import BusinessHours


def _today_local():
    return timezone.localtime(timezone.now()).date()


@pytest.mark.django_db(transaction=True)
def test_concurrent_booking_attempts_for_the_same_slot_only_one_succeeds():
    category = ServiceCategory.objects.create(name="Maquillaje Concurrencia")
    service = Service.objects.create(
        category=category, name="Servicio Concurrente", price="500.00", duration_minutes=60
    )
    target_date = _today_local() + timedelta(days=3)
    BusinessHours.objects.create(
        weekday=target_date.weekday(), start_time="09:00", end_time="18:00"
    )
    start = timezone.make_aware(datetime.combine(target_date, time(9, 0)))

    attempt_count = 8
    barrier = threading.Barrier(attempt_count)
    results = []
    results_lock = threading.Lock()

    def attempt(index):
        barrier.wait()  # maximize contention: every thread races at once
        try:
            create_appointment(
                service=service,
                start_datetime=start,
                customer_data={
                    "full_name": f"Cliente {index}",
                    "email": f"cliente{index}@example.com",
                    "phone": f"8888000{index}",
                },
            )
            outcome = "success"
        except SlotNotAvailableError:
            outcome = "failed"
        finally:
            connection.close()
        with results_lock:
            results.append(outcome)

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(attempt_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("success") == 1
    assert results.count("failed") == attempt_count - 1
    assert Appointment.objects.filter(service=service, start_datetime=start).count() == 1
