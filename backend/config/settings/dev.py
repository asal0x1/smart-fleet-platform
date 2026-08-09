"""Development settings."""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Dev'da OTP kodini konsolga chiqaramiz, SMS yubormaymiz
ESKIZ_MOCK = True

# Dev'da istalgan portdan (localhost:3000, :5173, :8080 ...) ulanish mumkin.
# base.py da bu DEBUG qiymatiga bog'liq edi, shuning uchun bu yerda aniq yozamiz.
CORS_ALLOW_ALL_ORIGINS = True
