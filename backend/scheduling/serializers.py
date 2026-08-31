from rest_framework import serializers

from scheduling.models import BlockedTime, BusinessHours, SpecialDate


class BusinessHoursPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHours
        fields = ["id", "weekday", "start_time", "end_time"]


class BusinessHoursAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHours
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        weekday = attrs.get("weekday", getattr(self.instance, "weekday", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))

        if start_time is not None and end_time is not None and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "La hora de fin debe ser posterior a la hora de inicio."}
            )

        if is_active and start_time is not None and end_time is not None:
            overlapping = BusinessHours.objects.filter(weekday=weekday, is_active=True)
            if self.instance is not None:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            overlapping = overlapping.filter(start_time__lt=end_time, end_time__gt=start_time)
            if overlapping.exists():
                raise serializers.ValidationError(
                    "Este horario se superpone con otro intervalo existente para el mismo día."
                )
        return attrs


class SpecialDateAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialDate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        is_closed = attrs.get("is_closed", getattr(self.instance, "is_closed", True))
        open_time = attrs.get(
            "special_open_time", getattr(self.instance, "special_open_time", None)
        )
        close_time = attrs.get(
            "special_close_time", getattr(self.instance, "special_close_time", None)
        )

        if not is_closed:
            if not open_time or not close_time:
                raise serializers.ValidationError(
                    "Si el día no está cerrado, debes indicar hora de apertura y cierre especiales."
                )
            if open_time >= close_time:
                raise serializers.ValidationError(
                    {"special_close_time": "La hora de cierre debe ser posterior a la de apertura."}
                )
        return attrs


class BlockedTimeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedTime
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_datetime", getattr(self.instance, "start_datetime", None))
        end = attrs.get("end_datetime", getattr(self.instance, "end_datetime", None))
        if start is not None and end is not None and start >= end:
            raise serializers.ValidationError(
                {"end_datetime": "La fecha y hora de fin debe ser posterior a la de inicio."}
            )
        return attrs
