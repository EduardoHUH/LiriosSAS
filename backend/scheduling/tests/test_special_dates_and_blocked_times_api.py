import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_admin_can_create_a_closed_holiday(staff_client):
    response = staff_client.post(
        "/api/v1/admin/special-dates/",
        {"date": "2026-12-25", "is_closed": True, "reason": "Navidad"},
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_admin_special_date_requires_open_and_close_time_when_not_closed(staff_client):
    response = staff_client.post(
        "/api/v1/admin/special-dates/",
        {"date": "2026-12-24", "is_closed": False},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_special_date_with_custom_hours_succeeds(staff_client):
    response = staff_client.post(
        "/api/v1/admin/special-dates/",
        {
            "date": "2026-12-24",
            "is_closed": False,
            "special_open_time": "09:00",
            "special_close_time": "13:00",
        },
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_admin_special_date_rejects_close_time_before_open_time(staff_client):
    response = staff_client.post(
        "/api/v1/admin/special-dates/",
        {
            "date": "2026-12-24",
            "is_closed": False,
            "special_open_time": "13:00",
            "special_close_time": "09:00",
        },
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_can_create_a_blocked_time_range(staff_client):
    response = staff_client.post(
        "/api/v1/admin/blocked-times/",
        {
            "start_datetime": "2026-09-01T14:00:00Z",
            "end_datetime": "2026-09-01T16:00:00Z",
            "reason": "Cita personal",
        },
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_admin_blocked_time_rejects_end_before_start_with_clean_400(staff_client):
    response = staff_client.post(
        "/api/v1/admin/blocked-times/",
        {
            "start_datetime": "2026-09-01T16:00:00Z",
            "end_datetime": "2026-09-01T14:00:00Z",
        },
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_blocked_times_admin_endpoint_requires_staff():
    client = APIClient()

    response = client.get("/api/v1/admin/blocked-times/")

    assert response.status_code == 401
