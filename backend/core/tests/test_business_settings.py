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
