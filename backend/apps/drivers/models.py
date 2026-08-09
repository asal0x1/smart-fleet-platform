from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.uploads import (
    car_photo_upload_to,
    driver_doc_upload_to,
    validate_image_file,
)
from apps.users.models import User


class Driver(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver"
    )
    car_model = models.CharField("Mashina modeli", max_length=100, blank=True)
    car_color = models.CharField("Rangi", max_length=50, blank=True)
    car_number = models.CharField("Davlat raqami", max_length=20, blank=True)
    license_number = models.CharField("Guvohnoma", max_length=50, blank=True)

    # --- Hujjatlar (tasdiqlash uchun) ---
    license_photo = models.ImageField(
        "Haydovchilik guvohnomasi", upload_to=driver_doc_upload_to,
        blank=True, null=True, validators=[validate_image_file],
    )
    tech_passport_photo = models.ImageField(
        "Texnik pasport", upload_to=driver_doc_upload_to,
        blank=True, null=True, validators=[validate_image_file],
    )
    passport_photo = models.ImageField(
        "Pasport", upload_to=driver_doc_upload_to,
        blank=True, null=True, validators=[validate_image_file],
    )
    car_photo = models.ImageField(
        "Mashina rasmi", upload_to=car_photo_upload_to,
        blank=True, null=True, validators=[validate_image_file],
    )

    is_active = models.BooleanField("Tasdiqlangan", default=False)
    is_online = models.BooleanField("Onlayn", default=False)

    # PostGIS nuqta (lng, lat tartibida saqlanadi)
    location = gis_models.PointField(
        "Joylashuv", geography=True, null=True, blank=True, srid=4326
    )

    rating = models.DecimalField(
        "Reyting", max_digits=2, decimal_places=1, default=5.0
    )
    total_trips = models.PositiveIntegerField("Safarlar", default=0)

    class Meta:
        db_table = "drivers"
        verbose_name = "Haydovchi"
        verbose_name_plural = "Haydovchilar"

    def __str__(self):
        return f"{self.user.full_name or self.user.phone} — {self.car_number}"

    # Tasdiqlash uchun majburiy hujjatlar
    REQUIRED_DOCUMENTS = ("license_photo", "tech_passport_photo")

    @property
    def missing_documents(self):
        """Tasdiqlash uchun yetishmayotgan hujjatlar ro'yxati."""
        return [
            self._meta.get_field(name).verbose_name
            for name in self.REQUIRED_DOCUMENTS
            if not getattr(self, name)
        ]

    @property
    def has_documents(self):
        return not self.missing_documents

    @property
    def current_lat(self):
        return self.location.y if self.location else None

    @property
    def current_lng(self):
        return self.location.x if self.location else None
