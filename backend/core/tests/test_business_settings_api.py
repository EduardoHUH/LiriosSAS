import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import BusinessSettings

User = get_user_model()

URL = "/api/v1/admin/business-settings/"


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_requires_staff():
    client = APIClient()

    response = client.get(URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_returns_the_singleton(staff_client):
    response = staff_client.get(URL)

    assert response.status_code == 200
    assert response.data["business_name"] == "Lirios"


@pytest.mark.django_db
def test_patch_updates_configurable_fields(staff_client):
    response = staff_client.patch(
        URL,
        {
            "business_name": "Lirios Beauty Studio",
            "contact_email": "hola@lirios.hn",
            "is_accepting_bookings": False,
            "cancellation_deadline_hours": 12,
            "reminder_hours_before": 48,
        },
    )

    assert response.status_code == 200, response.data
    settings_obj = BusinessSettings.load()
    assert settings_obj.business_name == "Lirios Beauty Studio"
    assert settings_obj.contact_email == "hola@lirios.hn"
    assert settings_obj.is_accepting_bookings is False
    assert settings_obj.cancellation_deadline_hours == 12
    assert settings_obj.reminder_hours_before == 48


@pytest.mark.django_db
def test_patch_cannot_change_read_only_fields(staff_client):
    original = BusinessSettings.load()

    response = staff_client.patch(URL, {"id": 999, "created_at": "2000-01-01T00:00:00Z"})

    assert response.status_code == 200
    settings_obj = BusinessSettings.load()
    assert settings_obj.id == original.id
    assert settings_obj.created_at == original.created_at
