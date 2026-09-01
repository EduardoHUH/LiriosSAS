from django.contrib import admin
from django.utils import timezone

from reviews.models import Review, ReviewStatus


@admin.action(description="Aprobar reseñas seleccionadas")
def approve_reviews(modeladmin, request, queryset):
    queryset.update(
        status=ReviewStatus.APPROVED, moderated_at=timezone.now(), moderated_by=request.user
    )


@admin.action(description="Rechazar reseñas seleccionadas")
def reject_reviews(modeladmin, request, queryset):
    queryset.update(
        status=ReviewStatus.REJECTED, moderated_at=timezone.now(), moderated_by=request.user
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["reviewer_name", "rating", "status", "appointment", "created_at"]
    list_filter = ["status", "rating"]
    search_fields = ["reviewer_name", "comment", "appointment__customer__full_name"]
    readonly_fields = ["appointment", "reviewer_name", "rating", "comment", "moderated_at", "moderated_by"]
    actions = [approve_reviews, reject_reviews]
