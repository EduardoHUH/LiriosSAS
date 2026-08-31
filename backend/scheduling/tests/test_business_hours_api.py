import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from scheduling.models import BusinessHours, Weekday

User = get_user_model()


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_public_business_hours_only_lists_active_intervals():
    BusinessHours.objects.create(
        weekday=Weekday.MONDAY, start_time="09:00", end_time="13:00", is_active=True
    )
    BusinessHours.objects.create(
        weekday=Weekday.TUESDAY, start_time="09:00", end_time="13:00", is_active=False
    )
    client = APIClient()

    response = client.get("/api/v1/business-hours/")

    weekdays = [item["weekday"] for item in response.data]
    assert response.status_code == 200
    assert Weekday.MONDAY in weekdays
    assert Weekday.TUESDAY not in weekdays


@pytest.mark.django_db
def test_admin_business_hours_requires_staff():
    client = APIClient()

    response = client.get("/api/v1/admin/business-hours/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_creating_without_is_active_defaults_to_active_not_silently_false(staff_client):
    """Regression guard: DRF's BooleanField treats a missing key as an
    unchecked HTML checkbox (silently False) under form/multipart parsing.
    The API must be JSON-only by default so omitting is_active means
    'use the model default (True)', not 'disable this interval'."""
    response = staff_client.post(
        "/api/v1/admin/business-hours/",
        {"weekday": Weekday.WEDNESDAY, "start_time": "09:00", "end_time": "13:00"},
    )

    assert response.status_code == 201, response.data
    assert response.data["is_active"] is True


@pytest.mark.django_db
def test_admin_can_create_a_second_non_overlapping_interval_same_day(staff_client):
    BusinessHours.objects.create(
        weekday=Weekday.MONDAY, start_time="09:00", end_time="13:00"
    )

    response = staff_client.post(
        "/api/v1/admin/business-hours/",
        {"weekday": Weekday.MONDAY, "start_time": "14:00", "end_time": "18:00"},
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_admin_create_rejects_overlapping_interval_same_day(staff_client):
    BusinessHours.objects.create(
        weekday=Weekday.MONDAY, start_time="09:00", end_time="13:00"
    )

    response = staff_client.post(
        "/api/v1/admin/business-hours/",
        {"weekday": Weekday.MONDAY, "start_time": "12:00", "end_time": "15:00"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_create_allows_overlapping_time_on_a_different_day(staff_client):
    BusinessHours.objects.create(
        weekday=Weekday.MONDAY, start_time="09:00", end_time="13:00"
    )

    response = staff_client.post(
        "/api/v1/admin/business-hours/",
        {"weekday": Weekday.TUESDAY, "start_time": "09:00", "end_time": "13:00"},
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_admin_create_rejects_end_time_before_start_time_with_clean_400(staff_client):
    response = staff_client.post(
        "/api/v1/admin/business-hours/",
        {"weekday": Weekday.MONDAY, "start_time": "13:00", "end_time": "09:00"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_updating_an_interval_does_not_flag_itself_as_overlapping(staff_client):
    interval = BusinessHours.objects.create(
        weekday=Weekday.MONDAY, start_time="09:00", end_time="13:00"
    )

    response = staff_client.patch(
        f"/api/v1/admin/business-hours/{interval.id}/", {"end_time": "13:30"}
    )

    assert response.status_code == 200, response.data
