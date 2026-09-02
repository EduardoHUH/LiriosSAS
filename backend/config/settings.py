"""
Django settings for the Lirios SAAS backend.

See https://docs.djangoproject.com/en/6.1/topics/settings/
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "anymail",
    "core",
    "accounts",
    "customers",
    "catalog",
    "scheduling",
    "appointments",
    "notifications",
    "reviews",
    "gallery",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# Individual DB_* vars (rather than a single DATABASE_URL) so a password
# containing URL-special characters (@, :, /) can't break parsing.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", default="lirios_saas"),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Tegucigalpa"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = "static/"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework
# Secure-by-default: every endpoint requires authentication unless a view
# explicitly opts into a public permission class. Authentication is JWT
# bearer tokens only (no session/cookie auth for the API) since the
# frontend and backend live on different domains. Django's own /admin/
# site is unaffected -- it uses its own session-based login separately.

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # JSON only by default. DRF's BooleanField treats a missing key as an
    # unchecked HTML checkbox (silently False) under form/multipart parsing,
    # which would let a client silently disable e.g. is_active by omitting
    # it. Multipart is opted back in explicitly only on the one view that
    # needs file uploads (ServiceAdminViewSet).
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
        "password_reset": "5/min",
        "booking_create": "20/hour",
        "appointment_action": "30/hour",
    },
    # DRF's built-in Throttled exception message is English-only ("Request
    # was throttled..."); every other user-facing error in this codebase is
    # Spanish, so it's translated here rather than left as
    # the one English leak in the API.
    "EXCEPTION_HANDLER": "core.exception_handlers.spanish_throttle_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}


# CORS
# Only the deployed frontend (and local dev server) may call this API from a browser.

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])

# Used to build links back to the app in emails (booking management link,
# password reset link).
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")


# Email
# SendGrid via django-anymail. Falls back to Django's console backend (prints
# instead of sending) when no API key is configured, so the app runs and
# tests pass with no real credentials -- only actual delivery needs one.

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Lirios <no-reply@lirios.hn>")
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")

if SENDGRID_API_KEY:
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
    ANYMAIL = {"SENDGRID_API_KEY": SENDGRID_API_KEY}
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
