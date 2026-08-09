"""Umumiy validatorlar — telefon raqam va koordinatalar.

Loyihada bir nechta joyda bir xil tekshiruv kerak bo'lgani uchun
shu yerda markazlashtirildi.
"""
import re

from rest_framework import serializers

# O'zbekiston telefon raqami: +998 + 9 ta raqam
PHONE_REGEX = re.compile(r"^\+998\d{9}$")

PHONE_ERROR = "Telefon raqam +998XXXXXXXXX ko'rinishida bo'lishi kerak"


def normalize_phone(value):
    """Bo'sh joy, tire, qavslarni olib tashlaydi va +998 ni to'ldiradi.

    Qabul qiladi:  '+998 90 123-45-67', '998901234567', '901234567'
    Qaytaradi:     '+998901234567'
    """
    if not value:
        return value

    digits = re.sub(r"[^\d+]", "", str(value))

    if digits.startswith("+"):
        cleaned = digits
    elif digits.startswith("998"):
        cleaned = "+" + digits
    elif len(digits) == 9:
        cleaned = "+998" + digits
    else:
        cleaned = "+" + digits

    return cleaned


def validate_phone(value):
    """Serializer uchun: normalizatsiya + tekshiruv. Xato bo'lsa ValidationError."""
    cleaned = normalize_phone(value)
    if not PHONE_REGEX.match(cleaned):
        raise serializers.ValidationError(PHONE_ERROR)
    return cleaned


class PhoneField(serializers.CharField):
    """`phone = PhoneField()` — avtomatik normalizatsiya qiladigan maydon."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 20)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return validate_phone(super().to_internal_value(data))


class LatitudeField(serializers.FloatField):
    def __init__(self, **kwargs):
        kwargs.setdefault("min_value", -90.0)
        kwargs.setdefault("max_value", 90.0)
        super().__init__(**kwargs)


class LongitudeField(serializers.FloatField):
    def __init__(self, **kwargs):
        kwargs.setdefault("min_value", -180.0)
        kwargs.setdefault("max_value", 180.0)
        super().__init__(**kwargs)
