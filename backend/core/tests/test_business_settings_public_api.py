import pytest
from rest_framework.test import APIClient

URL = "/api/v1/business-settings/"

PUBLIC_FIELDS = {
    "business_name",
    "contact_email",
    "contact_phone",
    "address",
    "social_links",
    "min_booking_notice_hours",
    "max_booking_window_days",
    "cancellation_deadline_hours",
    "unpaid_hold_minutes",
    "default_buffer_minutes",
    "is_accepting_bookings",
}


@pytest.mark.django_db
def test_get_requires_no_auth():
    client = APIClient()

    response = client.get(URL)

    assert response.status_code == 200
    assert response.data["business_name"] == "Lirios"


@pytest.mark.django_db
def test_response_exposes_only_the_public_field_set():
    client = APIClient()

    response = client.get(URL)

    assert set(response.data.keys()) == PUBLIC_FIELDS
    assert "id" not in response.data
    assert "created_at" not in response.data
    assert "updated_at" not in response.data
    assert "reminder_hours_before" not in response.data


@pytest.mark.django_db
def test_patch_is_not_allowed():
    client = APIClient()

    response = client.patch(URL, {"business_name": "Hacked"})

    assert response.status_code == 405
