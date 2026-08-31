import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

User = get_user_model()

REQUEST_URL = "/api/v1/auth/password-reset/"
CONFIRM_URL = "/api/v1/auth/password-reset/confirm/"


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="admin", email="admin@example.com", password="OldPassword123!", is_staff=True
    )


def _uid_and_token(user):
    return urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)


@pytest.mark.django_db
def test_request_reset_for_known_email_sends_email(staff_user):
    client = APIClient()

    response = client.post(REQUEST_URL, {"email": "admin@example.com"})

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["admin@example.com"]


@pytest.mark.django_db
def test_request_reset_for_unknown_email_returns_same_response_and_sends_nothing():
    client = APIClient()

    response = client.post(REQUEST_URL, {"email": "nadie@example.com"})

    assert response.status_code == 200
    assert response.data["detail"] == (
        "Si existe una cuenta con ese correo, se enviará un enlace de recuperación."
    )
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_request_reset_ignores_non_staff_accounts(db):
    User.objects.create_user(
        username="cliente", email="cliente@example.com", password="x", is_staff=False
    )
    client = APIClient()

    response = client.post(REQUEST_URL, {"email": "cliente@example.com"})

    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_request_reset_is_throttled_after_too_many_attempts(staff_user):
    client = APIClient()

    for _ in range(5):
        client.post(REQUEST_URL, {"email": "admin@example.com"})

    response = client.post(REQUEST_URL, {"email": "admin@example.com"})

    assert response.status_code == 429


@pytest.mark.django_db
def test_confirm_with_valid_token_changes_password(staff_user):
    uid, token = _uid_and_token(staff_user)
    client = APIClient()

    response = client.post(
        CONFIRM_URL, {"uid": uid, "token": token, "new_password": "BrandNewPassword456!"}
    )

    assert response.status_code == 200
    staff_user.refresh_from_db()
    assert staff_user.check_password("BrandNewPassword456!")


@pytest.mark.django_db
def test_confirm_with_invalid_token_returns_400_and_leaves_password_unchanged(staff_user):
    uid, _ = _uid_and_token(staff_user)
    client = APIClient()

    response = client.post(
        CONFIRM_URL, {"uid": uid, "token": "not-a-real-token", "new_password": "BrandNewPassword456!"}
    )

    assert response.status_code == 400
    staff_user.refresh_from_db()
    assert staff_user.check_password("OldPassword123!")


@pytest.mark.django_db
def test_confirm_with_malformed_uid_returns_400():
    client = APIClient()

    response = client.post(
        CONFIRM_URL,
        {"uid": "not-base64!!", "token": "whatever", "new_password": "BrandNewPassword456!"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_confirm_rejects_a_weak_password(staff_user):
    uid, token = _uid_and_token(staff_user)
    client = APIClient()

    response = client.post(CONFIRM_URL, {"uid": uid, "token": token, "new_password": "123"})

    assert response.status_code == 400
    staff_user.refresh_from_db()
    assert staff_user.check_password("OldPassword123!")


@pytest.mark.django_db
def test_token_cannot_be_reused_after_password_already_changed(staff_user):
    uid, token = _uid_and_token(staff_user)
    client = APIClient()
    client.post(CONFIRM_URL, {"uid": uid, "token": token, "new_password": "BrandNewPassword456!"})

    response = client.post(
        CONFIRM_URL, {"uid": uid, "token": token, "new_password": "AnotherPassword789!"}
    )

    assert response.status_code == 400
