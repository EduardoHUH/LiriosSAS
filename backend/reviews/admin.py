from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["reviewer_name", "rating", "status", "created_at"]
    list_filter = ["status", "rating"]
