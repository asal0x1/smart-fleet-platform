from django.db import models

from apps.common.models import TimeStampedModel
from apps.orders.models import Order


class PaymentMethod(models.TextChoices):
    CLICK = "click", "Click"
    PAYME = "payme", "Payme"
    CASH = "cash", "Naqd"


class PaymentState(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    PAID = "paid", "To'langan"
    FAILED = "failed", "Xato"
    CANCELLED = "cancelled", "Bekor qilindi"


class Payment(TimeStampedModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.PositiveIntegerField()
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=20, choices=PaymentState.choices, default=PaymentState.PENDING
    )
    # Tashqi tizim tranzaksiya IDsi (Click/Payme)
    transaction_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "payments"
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self):
        return f"Payment #{self.id} — {self.amount} ({self.status})"
