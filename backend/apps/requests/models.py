from django.db import models

from apps.common.models import TimeStampedModel
from apps.users.models import User


class RequestStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    CONTACTED = "contacted", "Bog'lanildi"
    CONFIRMED = "confirmed", "Tasdiqlandi"
    COMPLETED = "completed", "Yakunlandi"
    CANCELLED = "cancelled", "Bekor qilindi"


class HeavyEquipmentRequest(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("earth", "Yer ishlari"),
        ("lift", "Ko'tarish"),
        ("road", "Yo'l"),
        ("loader", "Yuklovchi"),
    ]

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="heavy_equipment_requests",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    items = models.JSONField(default=list)  # [{"name": ..., "quantity": ...}]
    address = models.CharField(max_length=255)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(default=1)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )

    estimated_price = models.PositiveIntegerField(
        "Taxminiy narx", null=True, blank=True
    )

    class Meta:
        db_table = "heavy_equipment_requests"
        verbose_name = "Og'ir texnika so'rovi"
        verbose_name_plural = "Og'ir texnika so'rovlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"HeavyEquip #{self.id} — {self.category}"


class WeddingRequest(TimeStampedModel):
    DECORATION_CHOICES = [
        ("flowers", "Gullar"),
        ("balloons", "Sharlar"),
        ("ribbons", "Lentalar"),
    ]

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="wedding_requests",
    )
    car_brand = models.CharField(max_length=100)
    car_count = models.PositiveIntegerField(default=1)
    decoration_type = models.CharField(max_length=20, choices=DECORATION_CHOICES, blank=True)
    address = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    duration_hours = models.PositiveIntegerField(default=1)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    estimated_price = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )

    class Meta:
        db_table = "wedding_requests"
        verbose_name = "To'y transporti so'rovi"
        verbose_name_plural = "To'y transporti so'rovlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Wedding #{self.id} — {self.car_brand} x{self.car_count}"


class PersonalDriverRequest(TimeStampedModel):
    EXPERIENCE_CHOICES = [
        ("1-3", "1-3 yil"),
        ("3-5", "3-5 yil"),
        ("5-10", "5-10 yil"),
        ("10+", "10 yildan ortiq"),
    ]
    DURATION_CHOICES = [
        ("1_day", "1 kun"),
        ("1_week", "1 hafta"),
        ("1_month", "1 oy"),
        ("3_months", "3 oy"),
        ("6_months", "6 oy"),
        ("1_year", "1 yil"),
    ]

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="personal_driver_requests",
    )
    car_brand = models.CharField(max_length=100)
    driver_experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES)
    contract_duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    address = models.CharField(max_length=255)
    start_date = models.DateField()
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    estimated_price = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )

    class Meta:
        db_table = "personal_driver_requests"
        verbose_name = "Shaxsiy haydovchi so'rovi"
        verbose_name_plural = "Shaxsiy haydovchi so'rovlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PersonalDriver #{self.id} — {self.car_brand} ({self.contract_duration})"


class BusRequest(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("wedding", "To'y va tantana"),
        ("memorial", "Maraka marosimi"),
        ("tour", "Tur va sayohat"),
    ]

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="bus_requests",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    bus_brand = models.CharField(max_length=100)
    bus_count = models.PositiveIntegerField(default=1)
    address = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    duration_hours = models.PositiveIntegerField(default=1)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    estimated_price = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )

    class Meta:
        db_table = "bus_requests"
        verbose_name = "Avtobus so'rovi"
        verbose_name_plural = "Avtobus so'rovlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Bus #{self.id} — {self.bus_brand} x{self.bus_count}"


class GiftMemorialRequest(TimeStampedModel):
    KIND_CHOICES = [
        ("gift", "Hadiya"),
        ("memorial", "Janoza / Maraka"),
    ]
    DECORATION_CHOICES = [
        ("flowers", "Gullar"),
        ("balloons", "Sharlar"),
        ("ribbons", "Lentalar"),
    ]

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="gift_memorial_requests",
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    decoration_type = models.CharField(max_length=20, choices=DECORATION_CHOICES, blank=True)
    address = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    estimated_price = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )

    class Meta:
        db_table = "gift_memorial_requests"
        verbose_name = "Hadiya/Maraka so'rovi"
        verbose_name_plural = "Hadiya/Maraka so'rovlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"GiftMemorial #{self.id} — {self.kind}"
