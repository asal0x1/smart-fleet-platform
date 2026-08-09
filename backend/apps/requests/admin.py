from django.contrib import admin, messages
from django.utils.html import format_html

from apps.common.admin_mixins import StatusColorMixin

from .models import (
    BusRequest,
    GiftMemorialRequest,
    HeavyEquipmentRequest,
    PersonalDriverRequest,
    RequestStatus,
    WeddingRequest,
)


class RequestStatusActionsMixin:
    """So'rov statusini bir bosishda o'zgartirish.

    Operator kuniga o'nlab so'rovni ko'radi — har birini ochib,
    status tanlab, saqlash juda sekin.
    """

    actions = ["mark_contacted", "mark_confirmed", "mark_completed",
               "mark_cancelled"]

    def _set_status(self, request, queryset, status, label):
        n = queryset.exclude(status=status).update(status=status)
        self.message_user(request, f"{n} ta so'rov '{label}' qilindi",
                          messages.SUCCESS)

    @admin.action(description="Holat: BOG'LANILDI")
    def mark_contacted(self, request, queryset):
        self._set_status(request, queryset, RequestStatus.CONTACTED,
                         "bog'lanildi")

    @admin.action(description="Holat: TASDIQLANDI")
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, RequestStatus.CONFIRMED,
                         "tasdiqlandi")

    @admin.action(description="Holat: YAKUNLANDI")
    def mark_completed(self, request, queryset):
        self._set_status(request, queryset, RequestStatus.COMPLETED,
                         "yakunlandi")

    @admin.action(description="Holat: BEKOR QILINDI")
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, RequestStatus.CANCELLED,
                         "bekor qilindi")


@admin.register(HeavyEquipmentRequest)
class HeavyEquipmentRequestAdmin(RequestStatusActionsMixin, StatusColorMixin,
                                 admin.ModelAdmin):
    list_display = [
        "id", "category", "items_display", "contact_name", "contact_phone",
        "start_date", "duration_days", "price_display",
        "status_badge", "created_at",
    ]
    list_filter = ["status", "category", "start_date", "created_at"]
    search_fields = ["id", "contact_name", "contact_phone", "address"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]

    fieldsets = (
        ("So'rov", {"fields": ("category", "items", "estimated_price", "status")}),
        ("Joy va vaqt", {
            "fields": ("address", "lat", "lng", "start_date", "start_time",
                       "duration_days")
        }),
        ("Aloqa", {"fields": ("contact_name", "contact_phone", "notes")}),
        ("Sanalar", {"classes": ("collapse",),
                     "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Taxminiy narx", ordering="estimated_price")
    def price_display(self, obj):
        if not obj.estimated_price:
            return "—"
        return f"{obj.estimated_price:,}".replace(",", " ")

    @admin.display(description="Texnikalar")
    def items_display(self, obj):
        if not obj.items:
            return "—"
        satr = ", ".join(
            f"{it.get('name')} ({it.get('quantity')})" for it in obj.items[:3]
        )
        if len(obj.items) > 3:
            satr += f" +{len(obj.items) - 3}"
        return format_html("<small>{}</small>", satr)


@admin.register(WeddingRequest)
class WeddingRequestAdmin(RequestStatusActionsMixin, StatusColorMixin,
                          admin.ModelAdmin):
    list_display = [
        "id", "car_brand", "car_count", "date", "duration_hours",
        "contact_name", "contact_phone", "price_display",
        "status_badge", "created_at",
    ]
    list_filter = ["status", "decoration_type", "date", "created_at"]
    search_fields = ["id", "contact_name", "contact_phone", "car_brand",
                     "address"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]

    fieldsets = (
        ("Buyurtma", {
            "fields": ("car_brand", "car_count", "decoration_type",
                       "estimated_price", "status")
        }),
        ("Joy va vaqt", {
            "fields": ("address", "date", "time", "duration_hours")
        }),
        ("Aloqa", {"fields": ("contact_name", "contact_phone", "notes")}),
        ("Sanalar", {"classes": ("collapse",),
                     "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Taxminiy narx", ordering="estimated_price")
    def price_display(self, obj):
        if not obj.estimated_price:
            return "—"
        return f"{obj.estimated_price:,}".replace(",", " ")


@admin.register(PersonalDriverRequest)
class PersonalDriverRequestAdmin(RequestStatusActionsMixin, StatusColorMixin,
                                 admin.ModelAdmin):
    list_display = [
        "id", "car_brand", "driver_experience", "contract_duration",
        "contact_name", "contact_phone", "price_display",
        "status_badge", "created_at",
    ]
    list_filter = ["status", "driver_experience", "contract_duration", "created_at"]
    search_fields = ["id", "contact_name", "contact_phone", "car_brand", "address"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]

    fieldsets = (
        ("So'rov", {
            "fields": ("car_brand", "driver_experience", "contract_duration",
                       "estimated_price", "status")
        }),
        ("Joy va vaqt", {"fields": ("address", "start_date")}),
        ("Aloqa", {"fields": ("contact_name", "contact_phone", "notes")}),
        ("Sanalar", {"classes": ("collapse",),
                     "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Taxminiy narx", ordering="estimated_price")
    def price_display(self, obj):
        if not obj.estimated_price:
            return "—"
        return f"{obj.estimated_price:,}".replace(",", " ")


@admin.register(BusRequest)
class BusRequestAdmin(RequestStatusActionsMixin, StatusColorMixin,
                      admin.ModelAdmin):
    list_display = [
        "id", "category", "bus_brand", "bus_count", "date",
        "contact_name", "contact_phone", "price_display",
        "status_badge", "created_at",
    ]
    list_filter = ["status", "category", "date", "created_at"]
    search_fields = ["id", "contact_name", "contact_phone", "bus_brand", "address"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]

    fieldsets = (
        ("So'rov", {
            "fields": ("category", "bus_brand", "bus_count",
                       "estimated_price", "status")
        }),
        ("Joy va vaqt", {"fields": ("address", "date", "time", "duration_hours")}),
        ("Aloqa", {"fields": ("contact_name", "contact_phone", "notes")}),
        ("Sanalar", {"classes": ("collapse",),
                     "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Taxminiy narx", ordering="estimated_price")
    def price_display(self, obj):
        if not obj.estimated_price:
            return "—"
        return f"{obj.estimated_price:,}".replace(",", " ")


@admin.register(GiftMemorialRequest)
class GiftMemorialRequestAdmin(RequestStatusActionsMixin, StatusColorMixin,
                               admin.ModelAdmin):
    list_display = [
        "id", "kind", "decoration_type", "date",
        "contact_name", "contact_phone", "price_display",
        "status_badge", "created_at",
    ]
    list_filter = ["status", "kind", "decoration_type", "date", "created_at"]
    search_fields = ["id", "contact_name", "contact_phone", "address"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]

    fieldsets = (
        ("So'rov", {
            "fields": ("kind", "decoration_type", "estimated_price", "status")
        }),
        ("Joy va vaqt", {"fields": ("address", "date", "time")}),
        ("Aloqa", {"fields": ("contact_name", "contact_phone", "notes")}),
        ("Sanalar", {"classes": ("collapse",),
                     "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Taxminiy narx", ordering="estimated_price")
    def price_display(self, obj):
        if not obj.estimated_price:
            return "—"
        return f"{obj.estimated_price:,}".replace(",", " ")
