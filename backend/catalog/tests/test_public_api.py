import pytest
from rest_framework.test import APIClient

from catalog.models import Service, ServiceCategory


@pytest.fixture
def active_category(db):
    return ServiceCategory.objects.create(name="Maquillaje Prueba", is_active=True)


@pytest.fixture
def inactive_category(db):
    return ServiceCategory.objects.create(name="Categoría Inactiva", is_active=False)


@pytest.mark.django_db
def test_public_categories_only_lists_active_ones(active_category, inactive_category):
    client = APIClient()

    response = client.get("/api/v1/categories/")

    names = [item["name"] for item in response.data["results"]] if "results" in response.data else [
        item["name"] for item in response.data
    ]
    assert response.status_code == 200
    assert active_category.name in names
    assert inactive_category.name not in names


@pytest.mark.django_db
def test_public_services_hides_inactive_service(active_category):
    Service.objects.create(
        category=active_category,
        name="Servicio activo",
        price="500.00",
        duration_minutes=60,
        is_active=True,
    )
    Service.objects.create(
        category=active_category,
        name="Servicio inactivo",
        price="500.00",
        duration_minutes=60,
        is_active=False,
    )
    client = APIClient()

    response = client.get("/api/v1/services/")

    names = [item["name"] for item in response.data]
    assert "Servicio activo" in names
    assert "Servicio inactivo" not in names


@pytest.mark.django_db
def test_public_services_hides_services_in_inactive_category(inactive_category):
    Service.objects.create(
        category=inactive_category,
        name="Servicio huérfano",
        price="500.00",
        duration_minutes=60,
    )
    client = APIClient()

    response = client.get("/api/v1/services/")

    names = [item["name"] for item in response.data]
    assert "Servicio huérfano" not in names


@pytest.mark.django_db
def test_public_services_can_be_filtered_by_category_slug(active_category):
    other_category = ServiceCategory.objects.create(name="Uñas Prueba")
    Service.objects.create(
        category=active_category, name="Maquillaje X", price="500", duration_minutes=60
    )
    Service.objects.create(
        category=other_category, name="Uñas X", price="500", duration_minutes=60
    )
    client = APIClient()

    response = client.get(f"/api/v1/services/?category={active_category.slug}")

    names = [item["name"] for item in response.data]
    assert names == ["Maquillaje X"]


@pytest.mark.django_db
def test_public_endpoints_require_no_authentication():
    client = APIClient()

    response = client.get("/api/v1/services/")

    assert response.status_code == 200
