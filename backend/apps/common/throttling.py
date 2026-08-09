"""Rate limiting (throttling).

Eng muhimi — OTP yuborish. Cheklovsiz bo'lsa bitta skript Eskiz
hisobini bir kechada bo'shatib yuboradi (har SMS pul turadi).

DIQQAT: throttle hisoblagichlari Django cache'da saqlanadi. Standart
LocMemCache har bir gunicorn worker uchun alohida bo'ladi, ya'ni
3 worker => cheklov amalda 3 barobar yumshoq. Prod'da Redis ulang
(settings/base.py dagi CACHES izohiga qarang).
"""
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle

from .validators import normalize_phone


class PhoneRateThrottle(SimpleRateThrottle):
    """So'rov tanasidagi `phone` bo'yicha cheklaydi (IP bo'yicha emas).

    IP bo'yicha cheklash yetarli emas: bitta hujumchi bir nechta IP'dan
    bitta raqamga SMS yog'dirishi mumkin. Aksincha, bitta uy Wi-Fi'sidan
    bir nechta odam ro'yxatdan o'tishi ham normal holat.
    """

    scope = "otp"

    def get_cache_key(self, request, view):
        phone = request.data.get("phone") if hasattr(request, "data") else None
        if not phone:
            return None  # phone yo'q -> serializer baribir 400 qaytaradi
        return self.cache_format % {
            "scope": self.scope,
            "ident": normalize_phone(phone),
        }


class OTPVerifyThrottle(PhoneRateThrottle):
    """Kodni brute-force qilishga qarshi (6 xonali kod = 1 000 000 variant)."""

    scope = "otp_verify"


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class RequestFormThrottle(AnonRateThrottle):
    """Og'ir texnika / to'y so'rovlari — spam formalarga qarshi."""

    scope = "request_form"


class PasswordResetThrottle(PhoneRateThrottle):
    scope = "password_reset"
