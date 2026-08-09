from django.contrib.gis.db import models as gis_models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.drivers.models import Driver
from apps.users.models import User


class Tariff(models.Model):
    name = models.CharField(max_length=50)
    name_uz = models.CharField(max_length=50, blank=True)
    base_fare = models.PositiveIntegerField("Boshlang'ich narx")
    per_km = models.PositiveIntegerField("Km narxi")
    per_minute = models.PositiveIntegerField("Daqiqa narxi")
    minimum_fare = models.PositiveIntegerField("Minimal narx")
    icon_url = models.URLField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tariffs"
        verbose_name = "Tarif"
        verbose_name_plural = "Tariflar"
        ordering = ["base_fare"]

    def __str__(self):
        return self.name

    def calculate_price(self, distance_km, duration_min):
        total = (
            self.base_fare
            + self.per_km * float(distance_km)
            + self.per_minute * int(duration_min)
        )
        return max(round(total), self.minimum_fare)


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    ACCEPTED = "accepted", "Qabul qilindi"
    DRIVER_ARRIVED = "driver_arrived", "Haydovchi yetib keldi"
    ONGOING = "ongoing", "Yo'lda"
    COMPLETED = "completed", "Yakunlandi"
    CANCELLED = "cancelled", "Bekor qilindi"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Naqd"
    CLICK = "click", "Click"
    PAYME = "payme", "Payme"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    PAID = "paid", "To'langan"
    FAILED = "failed", "Xato"


class Order(TimeStampedModel):
    client = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="orders",
    )
    tariff = models.ForeignKey(
        Tariff, on_delete=models.PROTECT, related_name="orders"
    )

    status = models.CharField(
        max_length=30, choices=OrderStatus.choices,
        default=OrderStatus.PENDING, db_index=True,
    )

    from_address = models.CharField(max_length=255)
    from_location = gis_models.PointField(geography=True, srid=4326)
    to_address = models.CharField(max_length=255)
    to_location = gis_models.PointField(geography=True, srid=4326)

    estimated_price = models.PositiveIntegerField(null=True, blank=True)
    final_price = models.PositiveIntegerField(null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    duration_min = models.PositiveIntegerField(null=True, blank=True)

    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    cancel_reason = models.TextField("Bekor qilish sababi", blank=True, default="")

    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.status}"

    @property
    def from_lat(self):
        return self.from_location.y if self.from_location else None

    @property
    def from_lng(self):
        return self.from_location.x if self.from_location else None

    @property
    def to_lat(self):
        return self.to_location.y if self.to_location else None

    @property
    def to_lng(self):
        return self.to_location.x if self.to_location else None


class ReviewKind(models.TextChoices):
    CLIENT_TO_DRIVER = "client_to_driver", "Mijozdan haydovchiga"
    DRIVER_TO_CLIENT = "driver_to_client", "Haydovchidan mijozga"


class Review(TimeStampedModel):
    """Safar yakunlangach beriladigan baho.

    Bir buyurtma uchun har tomon FAQAT BIR MARTA baho bera oladi
    (unique_together). Baho qo'yilgach haydovchi reytingi qayta hisoblanadi.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="reviews"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="written_reviews"
    )
    kind = models.CharField(max_length=20, choices=ReviewKind.choices)
    rating = models.PositiveSmallIntegerField(
        "Baho",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField("Izoh", blank=True)

    class Meta:
        db_table = "reviews"
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "kind"], name="uniq_review_per_order_kind"
            )
        ]

    def __str__(self):
        return f"#{self.order_id} — {self.rating}★"
