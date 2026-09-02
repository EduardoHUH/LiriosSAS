import io
import os

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


def make_oversized_image_upload(name="grande.jpg"):
    # Must be a valid, decodable image that's genuinely >5MB -- garbage
    # bytes fail Django's own "is this an image" check before our custom
    # size validator ever runs, and a solid-color image compresses far
    # below the cap regardless of canvas size, so this uses incompressible
    # random pixel data at a large enough canvas to guarantee the size.
    buffer = io.BytesIO()
    size = (1400, 1400)
    image = Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))
    image.save(buffer, format="PNG")
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


@pytest.mark.django_db
def test_upload_rejects_oversized_image(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/gallery/",
        {"category": category.id, "caption": "Grande", "image": make_oversized_image_upload()},
        format="multipart",
    )

    assert response.status_code == 400
    assert "image" in response.data


@pytest.mark.django_db
def test_upload_rejects_disallowed_image_format(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/gallery/",
        {
            "category": category.id,
            "caption": "Bmp",
            "image": make_image_upload(name="foto.bmp", format="BMP"),
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert "image" in response.data
