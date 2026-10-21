"""Django settings for local development and Vercel's Python runtime."""
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import AutoConfig, Csv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
config = AutoConfig(search_path=str(BASE_DIR))
IS_VERCEL = bool(os.getenv("VERCEL"))
SECRET_KEY = config("SECRET_KEY", default="")
if not SECRET_KEY:
    raise ImproperlyConfigured("Set SECRET_KEY in backend-drf/.env or the deployment environment.")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,testserver", cast=Csv())
for hostname in (os.getenv("VERCEL_URL"), os.getenv("VERCEL_PROJECT_PRODUCTION_URL")):
    if hostname and hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(hostname)

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "accounts", "api", "corsheaders", "rest_framework_simplejwt",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "stock_prediction_main.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug", "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "stock_prediction_main.wsgi.application"

database_url = config("DATABASE_URL", default="")
if IS_VERCEL and not database_url:
    raise ImproperlyConfigured("DATABASE_URL is required on Vercel; local SQLite is not persistent.")
DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=0, ssl_require=IS_VERCEL)} if database_url else {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"},
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:5173", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost:5173", cast=Csv())
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "120/min", "prediction": "6/min", "auth": "20/min"},
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), "REFRESH_TOKEN_LIFETIME": timedelta(days=1)}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = IS_VERCEL
CSRF_COOKIE_SECURE = IS_VERCEL
SECURE_SSL_REDIRECT = IS_VERCEL
SECURE_HSTS_SECONDS = 31536000 if IS_VERCEL else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_VERCEL
SECURE_HSTS_PRELOAD = IS_VERCEL
X_FRAME_OPTIONS = "DENY"
