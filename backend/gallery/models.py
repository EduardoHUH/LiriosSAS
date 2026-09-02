from django.db import models

from catalog.models import ServiceCategory
from core.models import TimeStampedModel
from core.validators import validate_image_file


class GalleryItem(TimeStampedModel):
    image = models.ImageField(upload_to="gallery/", validators=[validate_image_file])
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gallery_items",
    )
    caption = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Elemento de galería"
        verbose_name_plural = "Galería"
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.caption or f"Imagen #{self.pk}"
