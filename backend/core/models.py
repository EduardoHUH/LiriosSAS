from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base adding created/updated timestamps to a model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BusinessSettings(TimeStampedModel):
    """Singleton holding salon identity and centralized booking-rule config.

    Always access via BusinessSettings.load() rather than querying directly,
    so callers don't need to know the singleton row's primary key.
    """

    business_name = models.CharField(max_length=150, default="Lirios")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    social_links = models.JSONField(blank=True, default=dict)

    min_booking_notice_hours = models.PositiveIntegerField(default=2)
    max_booking_window_days = models.PositiveIntegerField(default=60)
    cancellation_deadline_hours = models.PositiveIntegerField(
        default=24,
        help_text="Also governs the reschedule deadline.",
    )
    unpaid_hold_minutes = models.PositiveIntegerField(
        default=20,
        help_text="How long a pending/awaiting-payment appointment holds its slot before auto-release.",
    )
    default_buffer_minutes = models.PositiveIntegerField(
        default=10,
        help_text="Used when a service does not set its own buffer_minutes.",
    )
    reminder_hours_before = models.PositiveIntegerField(
        default=24,
        help_text="How long before start_datetime a confirmed appointment's reminder email goes out.",
    )
    is_accepting_bookings = models.BooleanField(
        default=True,
        help_text="Global switch to pause new bookings without a deploy.",
    )

    class Meta:
        verbose_name = "Configuración del negocio"
        verbose_name_plural = "Configuración del negocio"

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        self.pk = 1
        if self._state.adding:
            existing = BusinessSettings.objects.filter(pk=1).only("created_at").first()
            if existing is not None:
                self.created_at = existing.created_at
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
