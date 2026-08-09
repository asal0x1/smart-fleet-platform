from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from apps.common.admin_mixins import admin_link, boolean_icon, image_preview

from .models import User
from .otp import OTPCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """BaseUserAdmin — parol xesh ko'rinishida chiqmaydi va
    admin'dan user yaratilganda parol to'g'ri hash qilinadi."""

    ordering = ["-created_at"]
    list_display = [
        "id", "phone", "full_name", "role", "driver_link",
        "orders_count", "verified_badge", "active_badge",
        "is_staff", "created_at",
    ]
    list_filter = ["role", "is_verified", "is_active", "is_staff", "created_at"]
    search_fields = ["id", "phone", "full_name", "email"]
    readonly_fields = ["created_at", "updated_at", "last_login",
                       "avatar_preview", "driver_link"]
    date_hierarchy = "created_at"
    list_per_page = 50
    actions = ["block_users", "unblock_users", "mark_verified"]

    # AbstractBaseUser'da username yo'q — fieldsets'ni phone'ga moslaymiz
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Shaxsiy ma'lumot", {
            "fields": ("full_name", "email",
                       ("avatar", "avatar_preview"), "avatar_url")
        }),
        ("Rol va holat", {
            "description": (
                "DIQQAT: bu yerdagi \"Faol\" (is_active) — hisobning "
                "TIZIMGA KIRA OLISHI (bloklangan/bloklanmagan). Haydovchini "
                "onlayn bo'lishga TASDIQLASH uchun bu YETARLI EMAS — "
                "pastdagi \"Haydovchi profili\" havolasi orqali Driver "
                "sahifasiga o'ting va u yerdagi \"Tasdiqlangan\" (Driver."
                "is_active) belgisini yoqing."
            ),
            "fields": ("role", "is_verified", "is_active", "driver_link"),
        }),
        (
            "Ruxsatlar",
            {
                "classes": ("collapse",),
                "fields": ("is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Sanalar", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "role", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("driver")
            .annotate(_orders=Count("orders"))
        )

    # --- Ustunlar ---
    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        return image_preview(obj.avatar, width=70)

    @admin.display(description="Haydovchi profili")
    def driver_link(self, obj):
        driver = getattr(obj, "driver", None)
        if driver is None:
            return "—"
        return admin_link(driver, driver.car_number or "profil")

    @admin.display(description="Buyurtmalar", ordering="_orders")
    def orders_count(self, obj):
        return obj._orders

    @admin.display(description="Tasdiqlangan", ordering="is_verified")
    def verified_badge(self, obj):
        return boolean_icon(obj.is_verified)

    @admin.display(description="Faol", ordering="is_active")
    def active_badge(self, obj):
        return boolean_icon(obj.is_active, "Faol", "Bloklangan")

    # --- Action'lar ---
    @admin.action(description="Tanlanganlarni BLOKLASH")
    def block_users(self, request, queryset):
        # O'zini va superuser'ni bloklash hisobdan chiqib qolishga olib keladi
        himoyalangan = queryset.filter(is_superuser=True).count()
        oziniki = queryset.filter(pk=request.user.pk).exists()

        n = (
            queryset.exclude(is_superuser=True)
            .exclude(pk=request.user.pk)
            .update(is_active=False)
        )
        self.message_user(request, f"{n} ta foydalanuvchi bloklandi",
                          messages.SUCCESS)
        if himoyalangan:
            self.message_user(
                request, f"{himoyalangan} ta superuser bloklanmadi",
                messages.WARNING,
            )
        if oziniki:
            self.message_user(request, "O'zingizni bloklab bo'lmaydi",
                              messages.WARNING)

    @admin.action(description="Blokdan CHIQARISH")
    def unblock_users(self, request, queryset):
        n = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"{n} ta foydalanuvchi blokdan chiqarildi",
                          messages.SUCCESS)

    @admin.action(description="Telefonni TASDIQLANGAN deb belgilash")
    def mark_verified(self, request, queryset):
        n = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(request, f"{n} ta raqam tasdiqlandi", messages.SUCCESS)


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ["phone", "code", "is_used", "expires_at", "created_at"]
    list_filter = ["is_used", "created_at"]
    search_fields = ["phone"]
    readonly_fields = ["phone", "code", "expires_at", "created_at"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
