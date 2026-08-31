import pytest
from django.db import IntegrityError

from customers.models import Customer


@pytest.mark.django_db
def test_email_must_be_unique():
    Customer.objects.create(full_name="Ana López", email="ana@example.com", phone="99999999")

    with pytest.raises(IntegrityError):
        Customer.objects.create(
            full_name="Ana López Otra", email="ana@example.com", phone="88888888"
        )
