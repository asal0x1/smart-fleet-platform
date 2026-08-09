"""
SMART FLEET — Base settings.
Barcha muhitlar uchun umumiy sozlamalar.
"""
import os
import platform
from datetime import timedelta
from pathlib import Path

import environ

# smart_fleet/config/settings/base.py -> BASE_DIR = smart_fleet/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# .env faylini o'qish (agar mavjud bo'lsa)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

if platform.system() == "Windows":
    OSGEO4W = env("OSGEO4W_ROOT", default=r"C:\OSGeo4W")
    os.environ.setdefault("OSGEO4W_ROOT", OSGEO4W)
    os.environ["PATH"] = os.path.join(OSGEO4W, "bin") + ";" + os.environ["PATH"]
    os.environ.setdefault("GDAL_DATA", os.path.join(OSGEO4W, "share", "gdal"))
    os.environ.setdefault("PROJ_LIB", os.path.join(OSGEO4W, "share", "proj"))

    GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH", default="")
    GEOS_LIBRARY_PATH = env("GEOS_LIBRARY_PATH", default="")
    if not GDAL_LIBRARY_PATH:
        del GDAL_LIBRARY_PATH  # avtomatik topsin
    if not GEOS_LIBRARY_PATH:
        del GEOS_LIBRARY_PATH

# --- Applications ---
DJANGO_APPS = [
    # daphne staticfiles'dan OLDIN turishi shart (daphne.E001)
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # PostGIS / GeoDjango
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.common",
    "apps.users",
    "apps.drivers",
    "apps.orders",
    "apps.payments",
    "apps.requests",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# --- Middleware ---
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

REDIS_URL = env("REDIS_URL", default="")

# --- Channels (WebSocket) ---
# Redis bo'lsa ishlatamiz; bo'lmasa xotiradagi layer (faqat dev/test uchun —
# u bitta jarayon ichida ishlaydi, gunicorn worker'lari o'rtasida emas)
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }


# --- Database (PostGIS) ---
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DB_NAME", default="smartfleet"),
        "USER": env("DB_USER", default="postgres"),
        "PASSWORD": env("DB_PASSWORD", default="postgres"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}


# --- Custom user model ---
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "apps.users.backends.PhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 6}},
]


# --- i18n ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True


# --- Static & media ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        # Umumiy fon cheklovi
        "anon": env("THROTTLE_ANON", default="60/min"),
        "user": env("THROTTLE_USER", default="300/min"),
        # Maxsus (apps/common/throttling.py dagi klasslar)
        "otp": env("THROTTLE_OTP", default="3/hour"),          # bitta raqamga SMS
        "otp_verify": env("THROTTLE_OTP_VERIFY", default="10/hour"),
        "login": env("THROTTLE_LOGIN", default="10/hour"),
        "register": env("THROTTLE_REGISTER", default="10/hour"),
        "request_form": env("THROTTLE_REQUEST_FORM", default="5/hour"),
        "password_reset": env("THROTTLE_PASSWORD_RESET", default="5/hour"),
        "geocode": env("THROTTLE_GEOCODE", default="60/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
}


# --- SimpleJWT ---
# Access token qisqa, refresh uzoq bo'lishi kerak.
# Ilgari access 7 kun edi — bunda logout deyarli ma'nosiz bo'ladi, chunki
# o'g'irlangan access token bir hafta ishlayveradi.
ACCESS_TOKEN_MINUTES = env.int("ACCESS_TOKEN_MINUTES", default=60)
REFRESH_TOKEN_DAYS = env.int("REFRESH_TOKEN_DAYS", default=30)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_TOKEN_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=REFRESH_TOKEN_DAYS),
    "ROTATE_REFRESH_TOKENS": True,
    # Logout va token rotatsiyasi ishlashi uchun majburiy
    "BLACKLIST_AFTER_ROTATION": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# --- drf-spectacular (Swagger) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "SMART FLEET API",
    "DESCRIPTION": "Taksi, og'ir texnika va to'y transporti marketplace API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# --- Cache (throttling hisoblagichlari shu yerda saqlanadi) ---
# DIQQAT: LocMemCache har bir gunicorn worker uchun alohida bo'ladi.
# 3 worker => OTP cheklovi amalda 3 barobar yumshoq. Prod'da Redis ulang:
#   REDIS_URL=redis://redis:6379/1
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "smartfleet-locmem",
        }
    }


# --- CORS ---
# Frontend (admin panel / veb-app) qaysi domenlardan API'ga ulana olishi.
# .env da vergul bilan ajratiladi:
#   CORS_ALLOWED_ORIGINS=https://admin.smartfleet.uz,https://smartfleet.uz
# DIQQAT: sxema (http:// yoki https://) majburiy, port bo'lsa u ham yoziladi,
# oxirida "/" BO'LMASIN — bo'lsa django-cors-headers xato beradi.
# Shuning uchun pastda oxirgi "/" avtomatik olib tashlanadi.
CORS_ALLOWED_ORIGINS = [
    origin.rstrip("/")
    for origin in env.list("CORS_ALLOWED_ORIGINS", default=[])
    if origin.strip()
]

# Vercel/Netlify preview deploy'lari uchun (ixtiyoriy):
#   CORS_ALLOWED_ORIGIN_REGEXES=^https://.*\.vercel\.app$
CORS_ALLOWED_ORIGIN_REGEXES = env.list("CORS_ALLOWED_ORIGIN_REGEXES", default=[])

# Dev'da hammaga ochiq, prod'da prod.py buni majburan False qiladi.
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)

# JWT "Authorization: Bearer ..." sarlavhasida keladi, cookie ishlatilmaydi —
# shuning uchun credentials shart emas. Cookie'ga o'tsangiz True qiling.
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=False)

# CORS sarlavhalari faqat API yo'llariga qo'shilsin (Django admin'ga emas)
CORS_URLS_REGEX = r"^/api/.*$"

# Django 4+ : HTTPS orqali kelgan POST (Django admin, form) uchun majburiy.
# Bo'sh qoldirsangiz prod.py uni CORS_ALLOWED_ORIGINS dan to'ldiradi.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


# =====================================================================
# Tashqi servislar (services/ papkasi shulardan foydalanadi)
# =====================================================================

# Eskiz.uz SMS (MOCK — hozircha haqiqiy SMS yubormaydi)
ESKIZ_MOCK = env.bool("ESKIZ_MOCK", default=True)
ESKIZ_EMAIL = env("ESKIZ_EMAIL", default="")
ESKIZ_PASSWORD = env("ESKIZ_PASSWORD", default="")
ESKIZ_BASE_URL = "https://notify.eskiz.uz/api"

# OTP sozlamalari
OTP_EXPIRE_SECONDS = env.int("OTP_EXPIRE_SECONDS", default=120)
OTP_LENGTH = 6

# Yandex Maps (REAL)
YANDEX_MAPS_API_KEY = env("YANDEX_MAPS_API_KEY", default="")

# OSRM route server (REAL — public server)
OSRM_BASE_URL = env("OSRM_BASE_URL", default="https://router.project-osrm.org")

# Click to'lov (REAL integration uchun)
CLICK_SERVICE_ID = env("CLICK_SERVICE_ID", default="")
CLICK_MERCHANT_ID = env("CLICK_MERCHANT_ID", default="")
CLICK_SECRET_KEY = env("CLICK_SECRET_KEY", default="")
CLICK_MERCHANT_USER_ID = env("CLICK_MERCHANT_USER_ID", default="")
# Webhook faqat shu IP'lardan qabul qilinadi. Bo'sh bo'lsa tekshiruv o'chiq
# (dev uchun). Prod'da Click bergan IP/CIDR ro'yxatini .env ga yozing:
#   CLICK_ALLOWED_IPS=213.230.106.0/24,185.74.5.10
CLICK_ALLOWED_IPS = env.list("CLICK_ALLOWED_IPS", default=[])

# --- To'y transporti ---
# Ilgari bu qiymat views.py da hardcoded edi — narx o'zgarsa deploy kerak edi
WEDDING_HOURLY_RATE = env.int("WEDDING_HOURLY_RATE", default=125_000)

# --- Og'ir texnika: kunlik narxlar (so'm) ---
# Kategoriya -> bir dona texnikaning kunlik narxi
HEAVY_EQUIPMENT_RATES = {
    "earth": env.int("HEAVY_RATE_EARTH", default=1_800_000),      # yer ishlari
    "lifting": env.int("HEAVY_RATE_LIFTING", default=2_500_000),  # ko'tarish
    "transport": env.int("HEAVY_RATE_TRANSPORT", default=1_200_000),
    "special": env.int("HEAVY_RATE_SPECIAL", default=3_000_000),
}
HEAVY_EQUIPMENT_DEFAULT_RATE = env.int("HEAVY_RATE_DEFAULT", default=1_500_000)

# --- Shaxsiy haydovchi: kunlik narx (so'm) ---
PERSONAL_DRIVER_DAILY_RATE = env.int("PERSONAL_DRIVER_DAILY_RATE", default=300_000)

# --- Avtobus: soatlik narx (so'm, bitta avtobus uchun) ---
BUS_HOURLY_RATE = env.int("BUS_HOURLY_RATE", default=200_000)

# --- Hadiya / Maraka: taxminiy bazaviy narx (so'm) ---
GIFT_BASE_PRICE = env.int("GIFT_BASE_PRICE", default=150_000)
MEMORIAL_BASE_PRICE = env.int("MEMORIAL_BASE_PRICE", default=100_000)

# --- Avtomatik haydovchi biriktirish ---
# Yangi buyurtma e'loni shu radiusdagi haydovchilarga ketadi
ORDER_BROADCAST_RADIUS_M = env.int("ORDER_BROADCAST_RADIUS_M", default=15_000)

# --- Geocoding ---
GEOCODE_CACHE_SECONDS = env.int("GEOCODE_CACHE_SECONDS", default=24 * 60 * 60)

# Email (og'ir texnika operatorga xabar)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
OPERATOR_EMAIL = env("OPERATOR_EMAIL", default="operator@smartfleet.uz")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@smartfleet.uz")
