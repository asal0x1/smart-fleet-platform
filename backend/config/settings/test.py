"""Test settings — pytest shu modul bilan ishlaydi.

Maqsad: testlar tez, deterministik va tashqi tarmoqqa bog'liq bo'lmasin.
"""
from .dev import *  # noqa

# Parol hash'lash testda vaqtning katta qismini yeydi (PBKDF2 ~ 300ms).
# MD5 faqat test uchun — prod'da hech qachon ishlatilmaydi.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Email xotirada to'planadi -> django.core.mail.outbox orqali tekshiriladi
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# SMS yuborilmaydi
ESKIZ_MOCK = True

# Tashqi servislar: conftest.py da tarmoq butunlay bloklanadi,
# bu yerdagi qiymatlar shunchaki tasodifan real API'ga chiqmaslik uchun
OSRM_BASE_URL = "http://osrm.invalid"
YANDEX_MAPS_API_KEY = ""

# Click imzosi deterministik bo'lishi uchun
CLICK_SERVICE_ID = "1"
CLICK_MERCHANT_ID = "1"
CLICK_SECRET_KEY = "test-secret"
CLICK_ALLOWED_IPS = []

# Throttle hisoblagichlari har test oldidan tozalanadi (conftest)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "smartfleet-test",
    }
}

# Migratsiyalar to'g'ri ishlashini ham tekshirmoqchimiz, shuning uchun
# MIGRATION_MODULES o'chirilmaydi.

# Test rasmlari loyihaning media/ papkasini iflos qilmasin
import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp(prefix="smartfleet-test-media-")

# WebSocket testlari uchun xotiradagi layer (Redis kerak emas)
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}
