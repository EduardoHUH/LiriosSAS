from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from accounts.views import MeView, StaffTokenObtainPairView

urlpatterns = [
    path("login/", StaffTokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
