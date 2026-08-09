import random
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class OTPCode(models.Model):
    """
    Telefon uchun bir martalik kod.
    Har telefon uchun eng oxirgi kod amal qiladi.
    """

    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_codes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone} — {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def generate(cls, phone):
        """Telefon uchun yangi OTP yaratadi (eskilarini o'chirmaydi, faqat yangisi amal qiladi)."""
        length = getattr(settings, "OTP_LENGTH", 6)
        code = "".join(str(random.randint(0, 9)) for _ in range(length))
        expire_seconds = getattr(settings, "OTP_EXPIRE_SECONDS", 120)
        expires_at = timezone.now() + timedelta(seconds=expire_seconds)

        # Eski tasdiqlanmagan kodlarni bekor qilamiz
        cls.objects.filter(phone=phone, is_used=False).update(is_used=True)

        return cls.objects.create(phone=phone, code=code, expires_at=expires_at)

    @classmethod
    def verify(cls, phone, code):
        """
        Kodni tekshiradi. To'g'ri bo'lsa is_used=True qilib True qaytaradi.
        """
        otp = (
            cls.objects.filter(phone=phone, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if otp is None or otp.is_expired:
            return False
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        return True
