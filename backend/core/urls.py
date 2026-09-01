from django.urls import path

from core.views import BusinessSettingsPublicView, health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("business-settings/", BusinessSettingsPublicView.as_view(), name="public-business-settings"),
]
