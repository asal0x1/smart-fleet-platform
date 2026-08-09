"""Production settings."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa

DEBUG = False

# Whitenoise — static fayllar uchun
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# --- Security ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# SSL o'rnatilgandan keyin .env da yoqing (nginx + sertifikat tayyor bo'lgach):
#   SECURE_SSL_REDIRECT=True
#   SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)  # noqa
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)  # noqa
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0


# =====================================================================
# CORS / CSRF
# =====================================================================
# Prod'da hech qachon hamma domenga ruxsat berilmaydi.
CORS_ALLOW_ALL_ORIGINS = False

# Eng ko'p uchraydigan xato: ro'yxat bo'sh qoladi va frontend
# "blocked by CORS policy" xatosini oladi, backend'da esa hech qanday
# belgi ko'rinmaydi. Shuning uchun ishga tushishda darrov to'xtatamiz.
if not CORS_ALLOWED_ORIGINS and not CORS_ALLOWED_ORIGIN_REGEXES:  # noqa
    raise ImproperlyConfigured(
        "CORS_ALLOWED_ORIGINS bo'sh — prod'da frontend API'ga ulana olmaydi.\n"
        ".env fayliga qo'shing, masalan:\n"
        "  CORS_ALLOWED_ORIGINS=https://admin.smartfleet.uz,https://smartfleet.uz"
    )

# CSRF alohida berilmagan bo'lsa, CORS ro'yxatidan olamiz.
# Bu Django admin'ning HTTPS orqali ishlashi uchun kerak (Django 4+).
if not CSRF_TRUSTED_ORIGINS:  # noqa
    CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)  # noqa


# --- Redis ---
# Redis'siz prod'da ikki narsa buziladi:
#   1. WebSocket xabarlari faqat bitta worker ichida qoladi — mijoz
#      boshqa worker'ga ulangan bo'lsa hech nima olmaydi
#   2. Throttle hisoblagichlari har worker'da alohida bo'ladi
if not REDIS_URL:  # noqa: F405
    import warnings

    warnings.warn(
        "REDIS_URL berilmagan. WebSocket ko'p worker'da ishlamaydi va "
        "throttle cheklovlari yumshaydi. .env ga qo'shing: "
        "REDIS_URL=redis://redis:6379/1",
        RuntimeWarning,
        stacklevel=2,
    )
