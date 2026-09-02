import io
import os

import pytest
from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework.test import APIClient

from appointments.models import Appointment
from catalog.models import Service, ServiceCategory
from customers.models import Customer

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
    # A solid-color image compresses far below the 5MB cap regardless of
    # pixel dimensions, so this needs to actually be a valid, decodable
    # image that's genuinely >5MB on disk -- random (incompressible) pixel
    # data at a large enough canvas size does that, unlike garbage bytes
    # (which just fail Django's own "is this an image at all" check before
    # our custom size validator ever runs).
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

    response = client.get("/api/v1/admin/services/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_endpoints_reject_non_staff_users():
    user = User.objects.create_user(username="cliente", password="x", is_staff=False)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/admin/services/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_create_a_service(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/services/",
        {
            "category": category.id,
            "name": "Maquillaje de novia",
            "price": "1200.00",
            "duration_minutes": 90,
        },
    )

    assert response.status_code == 201, response.data
    assert response.data["slug"] == "maquillaje-de-novia"
    assert Service.objects.filter(name="Maquillaje de novia").exists()


@pytest.mark.django_db
def test_admin_create_rejects_non_positive_price(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/services/",
        {
            "category": category.id,
            "name": "Servicio inválido",
            "price": "0.00",
            "duration_minutes": 60,
        },
    )

    assert response.status_code == 400
    assert "price" in response.data


@pytest.mark.django_db
def test_admin_create_with_valid_image_succeeds(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/services/",
        {
            "category": category.id,
            "name": "Con imagen",
            "price": "100.00",
            "duration_minutes": 30,
            "image": make_image_upload(),
        },
        format="multipart",
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_admin_create_rejects_non_image_file_disguised_as_jpg(staff_client, category):
    fake_image = io.BytesIO(b"this is not actually image data")
    fake_image.name = "fake.jpg"

    response = staff_client.post(
        "/api/v1/admin/services/",
        {
            "category": category.id,
            "name": "Imagen falsa",
            "price": "100.00",
            "duration_minutes": 30,
            "image": fake_image,
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert "image" in response.data


@pytest.mark.django_db
def test_admin_create_rejects_oversized_image(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/services/",
        {
            "category": category.id,
            "name": "Imagen grande",
            "price": "100.00",
            "duration_minutes": 30,
            "image": make_oversized_image_upload(),
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert "image" in response.data


@pytest.mark.django_db
def test_admin_create_rejects_disallowed_image_format(staff_client, category):
    response = staff_client.post(
        "/api/v1/admin/services/",
        {
            "category": category.id,
            "name": "Imagen bmp",
            "price": "100.00",
            "duration_minutes": 30,
            "image": make_image_upload(name="foto.bmp", format="BMP"),
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert "image" in response.data


@pytest.mark.django_db
def test_deleting_category_with_services_returns_conflict_not_500(staff_client, category):
    Service.objects.create(
        category=category, name="Servicio asociado", price="100", duration_minutes=30
    )

    response = staff_client.delete(f"/api/v1/admin/categories/{category.id}/")

    assert response.status_code == 409
    assert ServiceCategory.objects.filter(id=category.id).exists()


@pytest.mark.django_db
def test_deleting_service_with_appointments_returns_conflict_not_500(staff_client, category):
    service = Service.objects.create(
        category=category, name="Servicio con citas", price="100", duration_minutes=30
    )
    customer = Customer.objects.create(
        full_name="Ana López", email="ana@example.com", phone="99999999"
    )
    Appointment.objects.create(
        customer=customer,
        service=service,
        start_datetime="2026-09-01T14:00:00Z",
        end_datetime="2026-09-01T14:30:00Z",
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    response = staff_client.delete(f"/api/v1/admin/services/{service.id}/")

    assert response.status_code == 409
    assert Service.objects.filter(id=service.id).exists()


@pytest.mark.django_db
def test_admin_service_list_includes_inactive_services(staff_client, category):
    Service.objects.create(
        category=category, name="Inactivo visible para admin", price="100",
        duration_minutes=30, is_active=False,
    )

    response = staff_client.get("/api/v1/admin/services/")

    names = [item["name"] for item in response.data]
    assert "Inactivo visible para admin" in names
