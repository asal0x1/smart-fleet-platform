from django.contrib import admin as base_admin
from django.contrib import messages
from django.contrib.gis import admin
from django.db.models import Count

from apps.common.admin_mixins import admin_link, boolean_icon, image_preview

from .models import Driver


class ApprovalFilter(base_admin.SimpleListFilter):
    """Tasdiqlanmagan haydovchilarni bir bosishda ko'rish uchun."""

    title = "Tasdiq holati"
    parameter_name = "approval"

    def lookups(self, request, model_admin):
        return [
            ("pending", "Tasdiq kutmoqda"),
            ("approved", "Tasdiqlangan"),
            ("blocked", "Hisobi bloklangan"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "pending":
            return queryset.filter(is_active=False, user__is_active=True)
        if self.value() == "approved":
            return queryset.filter(is_active=True)
        if self.value() == "blocked":
            return queryset.filter(user__is_active=False)
        return queryset


@admin.register(Driver)
class DriverAdmin(admin.GISModelAdmin):
    list_display = [
        "id", "full_name", "phone", "car_display", "documents_badge",
        "approved_badge", "online_badge", "rating",
        "total_trips", "orders_count", "created_at",
    ]
    list_filter = [ApprovalFilter, "is_active", "is_online", "created_at"]
    search_fields = [
        "user__phone", "user__full_name", "car_number", "car_model",
        "license_number",
    ]
    autocomplete_fields = ["user"]
    readonly_fields = [
        "rating", "total_trips", "created_at", "updated_at",
        "license_preview", "tech_passport_preview", "passport_preview",
        "car_preview",
    ]
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ["-created_at"]
    actions = ["approve_drivers", "unapprove_drivers", "force_offline"]

    fieldsets = (
        ("Foydalanuvchi", {"fields": ("user",)}),
        ("Avtomobil", {
            "fields": ("car_model", "car_color", "car_number", "license_number")
        }),
        ("Hujjatlar", {
            "description": "Tasdiqlashdan oldin guvohnoma va texnik "
                           "pasportni tekshiring",
            "fields": (
                ("license_photo", "license_preview"),
                ("tech_passport_photo", "tech_passport_preview"),
                ("passport_photo", "passport_preview"),
                ("car_photo", "car_preview"),
            ),
        }),
        ("Holat", {
            "description": (
                "Haydovchini ONLAYN bo'lishga ruxsat berish uchun aynan "
                "shu yerdagi \"Tasdiqlangan\" (is_active) belgisini "
                "yoqing — Foydalanuvchi (User) sahifasidagi \"Faol\" "
                "boshqa narsa (hisobni bloklash/blokdan chiqarish)."
            ),
            "fields": ("is_active", "is_online"),
        }),
        ("Joylashuv", {"classes": ("collapse",), "fields": ("location",)}),
        ("Statistika", {
            "classes": ("collapse",),
            "fields": ("rating", "total_trips", "created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("user")
            .annotate(_orders=Count("orders"))
        )

    # --- Ustunlar ---
    @admin.display(description="F.I.O", ordering="user__full_name")
    def full_name(self, obj):
        return admin_link(obj.user, obj.user.full_name or "—")

    @admin.display(description="Telefon", ordering="user__phone")
    def phone(self, obj):
        return obj.user.phone

    @admin.display(description="Avtomobil")
    def car_display(self, obj):
        parts = [p for p in (obj.car_model, obj.car_number) if p]
        return " · ".join(parts) or "—"

    @admin.display(description="Hujjatlar")
    def documents_badge(self, obj):
        return boolean_icon(obj.has_documents, "To'liq", "Yetishmaydi")

    @admin.display(description="Guvohnoma")
    def license_preview(self, obj):
        return image_preview(obj.license_photo)

    @admin.display(description="Texpasport")
    def tech_passport_preview(self, obj):
        return image_preview(obj.tech_passport_photo)

    @admin.display(description="Pasport")
    def passport_preview(self, obj):
        return image_preview(obj.passport_photo)

    @admin.display(description="Mashina")
    def car_preview(self, obj):
        return image_preview(obj.car_photo)

    @admin.display(description="Tasdiq", ordering="is_active")
    def approved_badge(self, obj):
        return boolean_icon(obj.is_active, "Tasdiqlangan", "Kutmoqda")

    @admin.display(description="Onlayn", boolean=True, ordering="is_online")
    def online_badge(self, obj):
        return obj.is_online

    @admin.display(description="Buyurtmalar", ordering="_orders")
    def orders_count(self, obj):
        return obj._orders

    # --- Action'lar ---
    @admin.action(description="Tanlanganlarni TASDIQLASH")
    def approve_drivers(self, request, queryset):
        tasdiqlandi, otkazildi = 0, []

        for driver in queryset.select_related("user"):
            # Mashina raqamisiz tasdiqlash mantiqsiz — haydovchi buyurtma
            # olsa ham mijoz qaysi mashinani kutayotganini bilmaydi
            if not driver.car_number or not driver.has_documents:
                otkazildi.append(str(driver.id))
                continue
            if not driver.is_active:
                driver.is_active = True
                driver.save(update_fields=["is_active", "updated_at"])
            if not driver.user.is_verified:
                driver.user.is_verified = True
                driver.user.save(update_fields=["is_verified", "updated_at"])
            tasdiqlandi += 1

        if tasdiqlandi:
            self.message_user(
                request, f"{tasdiqlandi} ta haydovchi tasdiqlandi",
                messages.SUCCESS,
            )
        if otkazildi:
            self.message_user(
                request,
                f"Mashina raqami yoki hujjatlari yetishmagani uchun "
                f"o'tkazib yuborildi: #{', #'.join(otkazildi)}",
                messages.WARNING,
            )

    @admin.action(description="Tasdiqni BEKOR QILISH")
    def unapprove_drivers(self, request, queryset):
        n = 0
        for driver in queryset:
            driver.is_active = False
            driver.is_online = False
            driver.save(update_fields=["is_active", "is_online", "updated_at"])
            n += 1
        self.message_user(request, f"{n} ta haydovchi tasdig'i bekor qilindi",
                          messages.WARNING)

    @admin.action(description="Majburan OFFLINE qilish")
    def force_offline(self, request, queryset):
        n = queryset.filter(is_online=True).update(is_online=False)
        self.message_user(request, f"{n} ta haydovchi offline qilindi")
