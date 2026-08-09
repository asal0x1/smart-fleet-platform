from django.db import models

from apps.common.models import TimeStampedModel
from apps.users.models import User


class NotificationType(models.TextChoices):
    ORDER_CREATED = "order_created", "Yangi buyurtma"
    ORDER_ACCEPTED = "order_accepted", "Buyurtma qabul qilindi"
    DRIVER_ARRIVED = "driver_arrived", "Haydovchi yetib keldi"
    ORDER_STARTED = "order_started", "Safar boshlandi"
    ORDER_COMPLETED = "order_completed", "Safar yakunlandi"
    ORDER_CANCELLED = "order_cancelled", "Buyurtma bekor qilindi"
    PAYMENT_PAID = "payment_paid", "To'lov qabul qilindi"
    SYSTEM = "system", "Tizim xabari"


class Notification(TimeStampedModel):
    """Foydalanuvchiga yuborilgan xabar.

    WebSocket orqali darhol yuboriladi, lekin bazada ham saqlanadi —
    ilova yopiq bo'lsa foydalanuvchi keyin ko'radi.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=32, choices=NotificationType.choices)
    title = models.CharField(max_length=150)
    body = models.TextField(blank=True)
    # Ilova qaysi ekranga o'tishini bilishi uchun
    payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField("O'qilgan", default=False)

    class Meta:
        db_table = "notifications"
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user_id} — {self.type}"
