from django.db import models

from core.models import TimeStampedModel


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Lunes"
    TUESDAY = 1, "Martes"
    WEDNESDAY = 2, "Miércoles"
    THURSDAY = 3, "Jueves"
    FRIDAY = 4, "Viernes"
    SATURDAY = 5, "Sábado"
    SUNDAY = 6, "Domingo"


class BusinessHours(TimeStampedModel):
    """One open interval on one weekday. Multiple rows per weekday support
    split schedules (e.g. 09:00-13:00 and 14:00-18:00); no rows for a
    weekday means the business is closed that day."""

    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario de atención"
        verbose_name_plural = "Horarios de atención"
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="business_hours_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time}"


class SpecialDate(TimeStampedModel):
    """A holiday or one-off schedule exception overriding BusinessHours."""

    date = models.DateField(unique=True)
    is_closed = models.BooleanField(default=True)
    reason = models.CharField(max_length=150, blank=True)
    special_open_time = models.TimeField(
        null=True, blank=True, help_text="Only used when is_closed is False."
    )
    special_close_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Fecha especial"
        verbose_name_plural = "Fechas especiales"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} ({'cerrado' if self.is_closed else 'horario especial'})"


class BlockedTime(TimeStampedModel):
    """An ad-hoc block on the calendar: a partial-day range, a full day
    (00:00-23:59:59 the same day), or a multi-day range."""

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "Bloqueo de horario"
        verbose_name_plural = "Bloqueos de horario"
        ordering = ["start_datetime"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F("start_datetime")),
                name="blocked_time_end_after_start",
            )
        ]
        indexes = [models.Index(fields=["start_datetime", "end_datetime"])]

    def __str__(self):
        return f"{self.start_datetime} - {self.end_datetime}"
