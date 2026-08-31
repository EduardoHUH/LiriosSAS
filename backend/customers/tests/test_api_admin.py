from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatus
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
def customer(db):
    return Customer.objects.create(full_name="Ana López", email="ana@example.com", phone="99999999")


@pytest.fixture
def service(db):
    category = ServiceCategory.objects.create(name="Maquillaje Prueba")
    return Service.objects.create(
        category=category, name="Servicio de prueba", price="500.00", duration_minutes=60
    )


@pytest.mark.django_db
def test_admin_customers_require_staff():
    client = APIClient()

    response = client.get("/api/v1/admin/customers/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_can_list_customers(staff_client, customer):
    response = staff_client.get("/api/v1/admin/customers/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["email"] == "ana@example.com"
    assert response.data[0]["appointment_count"] == 0


@pytest.mark.django_db
def test_admin_search_filters_by_name_email_or_phone(staff_client, customer):
    Customer.objects.create(full_name="Beto Ruiz", email="beto@example.com", phone="88888888")

    response = staff_client.get("/api/v1/admin/customers/?search=ana@")

    assert len(response.data) == 1
    assert response.data[0]["id"] == customer.id


@pytest.mark.django_db
def test_admin_can_update_admin_notes(staff_client, customer):
    response = staff_client.patch(
        f"/api/v1/admin/customers/{customer.id}/", {"admin_notes": "Alérgica al látex"}
    )

    customer.refresh_from_db()
    assert response.status_code == 200
    assert customer.admin_notes == "Alérgica al látex"


@pytest.mark.django_db
def test_admin_can_create_customer(staff_client):
    response = staff_client.post(
        "/api/v1/admin/customers/",
        {"full_name": "Carla Díaz", "email": "carla@example.com", "phone": "77777777"},
    )

    assert response.status_code == 201, response.data
    assert Customer.objects.filter(email="carla@example.com").exists()


@pytest.mark.django_db
def test_admin_cannot_create_customer_with_duplicate_email(staff_client, customer):
    response = staff_client.post(
        "/api/v1/admin/customers/",
        {"full_name": "Otra Ana", "email": customer.email, "phone": "11111111"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_can_delete_customer_without_appointments(staff_client, customer):
    response = staff_client.delete(f"/api/v1/admin/customers/{customer.id}/")

    assert response.status_code == 204
    assert not Customer.objects.filter(id=customer.id).exists()


@pytest.mark.django_db
def test_admin_cannot_delete_customer_with_appointments(staff_client, customer, service):
    Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(days=1),
        end_datetime=timezone.now() + timedelta(days=1, hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    response = staff_client.delete(f"/api/v1/admin/customers/{customer.id}/")

    assert response.status_code == 409
    assert Customer.objects.filter(id=customer.id).exists()


@pytest.mark.django_db
def test_admin_customer_appointments_action_returns_history(staff_client, customer, service):
    appt = Appointment.objects.create(
        customer=customer,
        service=service,
        status=AppointmentStatus.CONFIRMED,
        start_datetime=timezone.now() + timedelta(days=1),
        end_datetime=timezone.now() + timedelta(days=1, hours=1),
        price_snapshot=service.price,
        duration_minutes_snapshot=service.duration_minutes,
    )

    response = staff_client.get(f"/api/v1/admin/customers/{customer.id}/appointments/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == appt.id
