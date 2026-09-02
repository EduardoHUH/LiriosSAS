from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/v1/admin/", include("core.admin_urls")),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/admin/", include("customers.admin_urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/admin/", include("catalog.admin_urls")),
    path("api/v1/", include("scheduling.urls")),
    path("api/v1/admin/", include("scheduling.admin_urls")),
    path("api/v1/", include("appointments.urls")),
    path("api/v1/admin/", include("appointments.admin_urls")),
    path("api/v1/", include("gallery.urls")),
    path("api/v1/admin/", include("gallery.admin_urls")),
    path("api/v1/", include("reviews.urls")),
    path("api/v1/admin/", include("reviews.admin_urls")),
]

# Wired directly to the underlying view rather than
# django.conf.urls.static.static() -- that helper has DEBUG=False baked in
# as a hard no-op (returns an empty urlpatterns list), regardless of any
# outer `if` around it, so it can't be reused for production serving. See
# the MEDIA_ROOT comment in config/settings.py for why this is served at
# all in production (no other serving story exists for runtime-uploaded
# photos, unlike the collected static/ files WhiteNoise handles).
urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
