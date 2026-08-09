from django.contrib import messages
from django.contrib.gis import admin
from django.db.models import Count
from django.utils.html import format_html

from apps.common.admin_mixins import StatusColorMixin, admin_link
from apps.payments.models import Payment

from .models import Order, OrderStatus, Review, Tariff


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = [
        "id", "name", "base_fare", "per_km", "per_minute",
        "minimum_fare", "orders_count", "is_active",
    ]
    list_filter = ["is_active"]
    list_editable = ["is_active"]
    # autocomplete_fields Order'da ishlashi uchun search_fields majburiy
    search_fields = ["name", "name_uz"]
    ordering = ["id"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_orders=Count("orders"))

    @admin.display(description="Buyurtmalar", ordering="_orders")
    def orders_count(self, obj):
        return obj._orders


class PaymentInline(admin.TabularInline):
    """To'lovlarni buyurtma sahifasida ko'rsatadi.

    Ilgari operator to'lovni tekshirish uchun alohida bo'limga o'tishi kerak edi.
    """

    model = Payment
    extra = 0
    can_delete = False
    fields = ["id", "amount", "method", "status", "transaction_id", "created_at"]
    readonly_fields = ["id", "created_at"]
    show_change_link = True


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    can_delete = False
    fields = ["kind", "rating", "comment", "author", "created_at"]
    readonly_fields = ["kind", "author", "created_at"]


@admin.register(Order)
class OrderAdmin(StatusColorMixin, admin.GISModelAdmin):
    list_display = [
        "id", "client_link", "driver_link", "status_badge",
        "route", "price", "payment_badge", "created_at",
    ]
    list_filter = [
        "status", "payment_method", "payment_status", "tariff", "created_at",
    ]
    search_fields = [
        "id", "from_address", "to_address",
        "client__phone", "client__full_name",
        "driver__user__phone", "driver__car_number",
    ]
    # 10 000 ta user bo'lganda oddiy select admin sahifasini qotirib qo'yadi
    autocomplete_fields = ["client", "driver", "tariff"]
    readonly_fields = [
        "created_at", "updated_at", "accepted_at", "started_at", "completed_at",
        "distance_km", "duration_min",
    ]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]
    inlines = [PaymentInline, ReviewInline]
    actions = ["cancel_orders"]

    fieldsets = (
        ("Ishtirokchilar", {"fields": ("client", "driver", "tariff")}),
        ("Holat", {"fields": ("status", "cancel_reason")}),
        ("Manzillar", {
            "fields": ("from_address", "from_location", "to_address", "to_location")
        }),
        ("Narx", {
            "fields": (
                "estimated_price", "final_price", "distance_km", "duration_min",
                "payment_method", "payment_status",
            )
        }),
        ("Sanalar", {
            "classes": ("collapse",),
            "fields": (
                "created_at", "accepted_at", "started_at", "completed_at",
                "updated_at",
            ),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "client", "driver__user", "tariff"
        )

    # --- Ustunlar ---
    @admin.display(description="Mijoz", ordering="client__full_name")
    def client_link(self, obj):
        return admin_link(obj.client, obj.client.full_name or obj.client.phone)

    @admin.display(description="Haydovchi")
    def driver_link(self, obj):
        if obj.driver is None:
            return format_html('<span style="color:#f59e0b">biriktirilmagan</span>')
        return admin_link(obj.driver, obj.driver.user.full_name or obj.driver.car_number)

    @admin.display(description="Marshrut")
    def route(self, obj):
        return format_html(
            "<small>{} → {}</small>",
            (obj.from_address or "—")[:28],
            (obj.to_address or "—")[:28],
        )

    @admin.display(description="Narx", ordering="estimated_price")
    def price(self, obj):
        summa = obj.final_price or obj.estimated_price or 0
        return f"{summa:,}".replace(",", " ")

    @admin.display(description="To'lov", ordering="payment_status")
    def payment_badge(self, obj):
        color = "#22c55e" if obj.payment_status == "paid" else "#f59e0b"
        return format_html(
            '<span style="color:{}">{} · {}</span>',
            color, obj.get_payment_method_display(),
            obj.get_payment_status_display(),
        )

    # --- Action'lar ---
    @admin.action(description="Tanlangan buyurtmalarni BEKOR QILISH")
    def cancel_orders(self, request, queryset):
        """Yakuniy holatdagi buyurtmalarga tegmaydi."""
        yopiq = (OrderStatus.COMPLETED, OrderStatus.CANCELLED)
        bekor, otkazildi = 0, 0

        for order in queryset:
            if order.status in yopiq:
                otkazildi += 1
                continue
            order.status = OrderStatus.CANCELLED
            if not order.cancel_reason:
                order.cancel_reason = "Admin panel orqali bekor qilindi"
            order.save(update_fields=["status", "cancel_reason", "updated_at"])
            bekor += 1

        Payment.objects.filter(
            order__in=queryset, status="pending"
        ).update(status="cancelled")

        if bekor:
            self.message_user(request, f"{bekor} ta buyurtma bekor qilindi",
                              messages.SUCCESS)
        if otkazildi:
            self.message_user(
                request,
                f"{otkazildi} tasi allaqachon yakunlangan/bekor qilingan — "
                f"tegilmadi",
                messages.WARNING,
            )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "order_link", "kind", "rating", "short_comment",
                    "author", "created_at"]
    list_filter = ["kind", "rating", "created_at"]
    search_fields = ["order__id", "comment", "author__phone",
                     "author__full_name"]
    autocomplete_fields = ["order", "author"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "author")

    @admin.display(description="Buyurtma", ordering="order__id")
    def order_link(self, obj):
        return admin_link(obj.order, f"#{obj.order_id}")

    @admin.display(description="Izoh")
    def short_comment(self, obj):
        return (obj.comment[:60] + "…") if len(obj.comment) > 60 else (obj.comment or "—")

    def has_add_permission(self, request):
        return False
