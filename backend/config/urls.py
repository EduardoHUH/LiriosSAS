from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/admin/", include("catalog.admin_urls")),
    path("api/v1/", include("scheduling.urls")),
    path("api/v1/admin/", include("scheduling.admin_urls")),
    path("api/v1/", include("appointments.urls")),
    path("api/v1/admin/", include("appointments.admin_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
