from django.db import models

from core.models import TimeStampedModel


class Customer(TimeStampedModel):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, db_index=True)
    admin_notes = models.TextField(
        blank=True,
        help_text="Private. Never expose through a customer-facing or public API.",
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
