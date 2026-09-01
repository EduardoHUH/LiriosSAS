import io

import pytest
from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework.test import APIClient

from catalog.models import ServiceCategory
from gallery.models import GalleryItem

User = get_user_model()


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(username="admin", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def category(db):
    return ServiceCategory.objects.create(name="Maquillaje Prueba")


def make_image_upload(name="foto.jpg", size=(10, 10), format="JPEG"):
    buffer = io.BytesIO()
    Image.new("RGB", size, color="red").save(buffer, format=format)
    buffer.seek(0)
    buffer.name = name
    return buffer


@pytest.mark.django_db
def test_admin_endpoints_require_authentication():
    client = APIClient()

    response = client.get("/api/v1/admin/gallery/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_endpoints_reject_non_staff_users():
    user = User.objects.create_user(username="cliente", password="x", is_staff=False)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/admin/gallery/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_can_upload_gallery_item(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/gallery/",
        {"category": category.id, "caption": "Nueva foto", "image": make_image_upload()},
        format="multipart",
    )

    assert response.status_code == 201, response.data
    assert GalleryItem.objects.count() == 1


@pytest.mark.django_db
def test_upload_rejects_a_non_image_file(staff_client, category):
    fake = io.BytesIO(b"not an image")
    fake.name = "foto.jpg"

    response = staff_client.post(
        "/api/v1/admin/gallery/",
        {"category": category.id, "caption": "Falsa", "image": fake},
        format="multipart",
    )

    assert response.status_code == 400
    assert "image" in response.data
