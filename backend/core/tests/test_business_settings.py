import pytest

from core.models import BusinessSettings


@pytest.mark.django_db
def test_load_returns_same_singleton_row_every_time():
    first = BusinessSettings.load()
    first.business_name = "Lirios Spa"
    first.save()

    second = BusinessSettings.load()

    assert second.pk == 1
    assert second.business_name == "Lirios Spa"
    assert BusinessSettings.objects.count() == 1


@pytest.mark.django_db
def test_save_always_forces_primary_key_to_one():
    settings_obj = BusinessSettings(business_name="Otro nombre")
    settings_obj.save()

    assert settings_obj.pk == 1
    assert BusinessSettings.objects.count() == 1


@pytest.mark.django_db
def test_delete_is_a_no_op():
    # The singleton row every slot-touching transaction locks
    # (_acquire_booking_lock in appointments/services.py) must never
    # actually disappear, so delete() is deliberately inert rather than
    # deferring to Django's default hard-delete behavior.
    settings_obj = BusinessSettings.load()

    settings_obj.delete()

    assert BusinessSettings.objects.filter(pk=1).exists()
