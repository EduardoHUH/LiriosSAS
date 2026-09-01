import pytest
from rest_framework.test import APIClient

from catalog.models import ServiceCategory
from gallery.models import GalleryItem


@pytest.fixture
def category(db):
    return ServiceCategory.objects.create(name="Maquillaje Prueba")


@pytest.fixture
def other_category(db):
    return ServiceCategory.objects.create(name="Uñas Prueba")


@pytest.mark.django_db
def test_only_active_items_are_listed(category):
    GalleryItem.objects.create(category=category, caption="Activa", is_active=True)
    GalleryItem.objects.create(category=category, caption="Inactiva", is_active=False)
    client = APIClient()

    response = client.get("/api/v1/gallery/")

    assert response.status_code == 200
    captions = [item["caption"] for item in response.data]
    assert captions == ["Activa"]


@pytest.mark.django_db
def test_category_filter(category, other_category):
    GalleryItem.objects.create(category=category, caption="Maquillaje")
    GalleryItem.objects.create(category=other_category, caption="Uñas")
    client = APIClient()

    response = client.get(f"/api/v1/gallery/?category={category.slug}")

    assert response.status_code == 200
    assert [item["caption"] for item in response.data] == ["Maquillaje"]


@pytest.mark.django_db
def test_item_exposes_nested_category(category):
    GalleryItem.objects.create(category=category, caption="Con categoría")
    client = APIClient()

    response = client.get("/api/v1/gallery/")

    assert response.data[0]["category"]["slug"] == category.slug
