from django.contrib import admin
from django.db.models import Sum

from apps.common.admin_mixins import StatusColorMixin, admin_link

from .models import Payment, PaymentState


@admin.register(Payment)
class PaymentAdmin(StatusColorMixin, admin.ModelAdmin):
    list_display = [
        "id", "order_link", "client", "amount_display",
        "method", "status_badge", "transaction_id", "created_at",
    ]
    list_filter = ["method", "status", "created_at"]
    search_fields = [
        "id", "order__id", "transaction_id",
        "order__client__phone", "order__client__full_name",
    ]
    autocomplete_fields = ["order"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order__client")

    def changelist_view(self, request, extra_context=None):
        """Sarlavhada filtrga mos umumiy summani ko'rsatadi."""
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response

        jami = qs.aggregate(
            tolangan=Sum("amount", filter=None) if False else Sum("amount"),
        )["tolangan"] or 0
        tolangan = qs.filter(status=PaymentState.PAID).aggregate(
            s=Sum("amount")
        )["s"] or 0
        response.context_data["title"] = (
            f"To'lovlar — jami {jami:,} so'm, to'langan {tolangan:,} so'm"
        ).replace(",", " ")
        return response

    @admin.display(description="Buyurtma", ordering="order__id")
    def order_link(self, obj):
        return admin_link(obj.order, f"#{obj.order_id}")

    @admin.display(description="Mijoz")
    def client(self, obj):
        return obj.order.client.full_name or obj.order.client.phone

    @admin.display(description="Summa", ordering="amount")
    def amount_display(self, obj):
        return f"{obj.amount:,}".replace(",", " ")

    def has_add_permission(self, request):
        """To'lov qo'lda yaratilmaydi — Click webhook orqali keladi."""
        return False
