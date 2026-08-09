"""Rasm yuklash uchun yo'l generatorlari va validatorlar.

Loyihada ilgari birorta ImageField yo'q edi — haydovchi hujjatlari
umuman yuklanmasdi va admin "tasdiqlash" tugmasini nimani ko'rib
bosishi noma'lum edi.
"""
import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils import timezone

# 5 MB — telefon kamerasidagi rasm uchun yetarli
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def _upload_to(prefix, instance, filename):
    """media/<prefix>/<yil>/<oy>/<uuid>.<kengaytma>

    Original nom ishlatilmaydi: unda foydalanuvchi ismi yoki
    boshqa shaxsiy ma'lumot bo'lishi mumkin, bundan tashqari
    bir xil nomli fayllar bir-birini almashtirib yuborardi.
    """
    ext = Path(filename).suffix.lower() or ".jpg"
    now = timezone.now()
    return f"{prefix}/{now:%Y/%m}/{uuid.uuid4().hex}{ext}"


def avatar_upload_to(instance, filename):
    return _upload_to("avatars", instance, filename)


def driver_doc_upload_to(instance, filename):
    return _upload_to("driver_docs", instance, filename)


def car_photo_upload_to(instance, filename):
    return _upload_to("car_photos", instance, filename)


def validate_image_file(value):
    """Hajm va kengaytmani tekshiradi.

    Pillow rasm ekanini o'zi tekshiradi (ImageField), bu yerda
    faqat hajm va kengaytma cheklovi.
    """
    if value.size > MAX_IMAGE_SIZE:
        mb = MAX_IMAGE_SIZE // (1024 * 1024)
        raise ValidationError(f"Rasm hajmi {mb} MB dan oshmasligi kerak")

    ext = Path(value.name).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        ruxsat = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(f"Ruxsat etilgan formatlar: {ruxsat}")
    return value


def absolute_media_url(request, field):
    """FileField -> to'liq URL (frontend uchun) yoki None."""
    if not field:
        return None
    url = field.url
    if request is not None:
        return request.build_absolute_uri(url)
    return url
