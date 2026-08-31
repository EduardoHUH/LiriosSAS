from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel


class ServiceCategory(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría de servicio"
        verbose_name_plural = "Categorías de servicio"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(TimeStampedModel):
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.PROTECT, related_name="services"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()
    buffer_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Blocks this much time after the appointment. Leave blank to use the business default.",
    )
    image = models.ImageField(upload_to="services/", blank=True)
    preparation_instructions = models.TextField(blank=True)
    cancellation_policy_notes = models.TextField(
        blank=True,
        help_text="Informational text shown to the customer. Enforced cancellation rules live in BusinessSettings.",
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this service is shown at all."
    )
    is_bookable = models.BooleanField(
        default=True, help_text="Whether this service currently accepts new bookings."
    )
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
