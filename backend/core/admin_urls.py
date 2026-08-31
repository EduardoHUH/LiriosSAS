from django.urls import path

from core.views import BusinessSettingsAdminView, dashboard_overview

urlpatterns = [
    path("business-settings/", BusinessSettingsAdminView.as_view(), name="admin-business-settings"),
    path("dashboard/overview/", dashboard_overview, name="admin-dashboard-overview"),
]
