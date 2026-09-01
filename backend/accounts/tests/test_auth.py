import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
ME_URL = "/api/v1/auth/me/"


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="admin", password="S3guraContrasena!", is_staff=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="cliente", password="S3guraContrasena!", is_staff=False
    )


@pytest.mark.django_db
def test_staff_login_returns_access_and_refresh_tokens(staff_user):
    client = APIClient()

    response = client.post(
        LOGIN_URL, {"username": "admin", "password": "S3guraContrasena!"}
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


SPANISH_NO_ACCOUNT_MESSAGE = "No se encontró una cuenta activa con las credenciales proporcionadas."


@pytest.mark.django_db
def test_login_rejects_non_staff_user(regular_user):
    client = APIClient()

    response = client.post(
        LOGIN_URL, {"username": "cliente", "password": "S3guraContrasena!"}
    )

    assert response.status_code == 401
    assert "access" not in response.data
    assert response.data["detail"] == SPANISH_NO_ACCOUNT_MESSAGE


@pytest.mark.django_db
def test_login_rejects_wrong_password(staff_user):
    client = APIClient()

    response = client.post(LOGIN_URL, {"username": "admin", "password": "wrong"})

    assert response.status_code == 401
    assert response.data["detail"] == SPANISH_NO_ACCOUNT_MESSAGE


@pytest.mark.django_db
def test_login_rejects_nonexistent_username():
    """Regression test: SimpleJWT's own credential check used to raise its
    English default message here, before StaffTokenObtainPairSerializer's
    own (Spanish) non-staff check ever ran -- both paths must now agree."""
    client = APIClient()

    response = client.post(LOGIN_URL, {"username": "no-existe", "password": "wrong"})

    assert response.status_code == 401
    assert response.data["detail"] == SPANISH_NO_ACCOUNT_MESSAGE


@pytest.mark.django_db
def test_me_requires_authentication():
    client = APIClient()

    response = client.get(ME_URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_staff_user(staff_user):
    client = APIClient()
    login_response = client.post(
        LOGIN_URL, {"username": "admin", "password": "S3guraContrasena!"}
    )
    access_token = login_response.data["access"]

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["username"] == "admin"
    assert response.data["is_staff"] is True


@pytest.mark.django_db
def test_refresh_token_issues_a_new_access_token(staff_user):
    client = APIClient()
    login_response = client.post(
        LOGIN_URL, {"username": "admin", "password": "S3guraContrasena!"}
    )
    refresh_token = login_response.data["refresh"]

    response = client.post(REFRESH_URL, {"refresh": refresh_token})

    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_login_is_throttled_after_too_many_attempts(staff_user):
    client = APIClient()

    for _ in range(5):
        client.post(LOGIN_URL, {"username": "admin", "password": "wrong"})

    response = client.post(LOGIN_URL, {"username": "admin", "password": "wrong"})

    assert response.status_code == 429
