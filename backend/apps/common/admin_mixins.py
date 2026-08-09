"""Admin klasslari uchun umumiy yordamchi vositalar."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


def admin_link(obj, label=None):
    """Boshqa modeldagi obyektga havola yasaydi."""
    if obj is None:
        return "—"
    url = reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=[obj.pk],
    )
    return format_html('<a href="{}">{}</a>', url, label or str(obj))


def boolean_icon(value, true_text="Ha", false_text="Yo'q"):
    color = "#22c55e" if value else "#ef4444"
    return format_html('<b style="color:{}">{}</b>', color,
                       true_text if value else false_text)


class StatusColorMixin:
    """Status ustunini rangli nishon ko'rinishida chiqaradi."""

    COLORS = {
        "pending": "#f59e0b",
        "accepted": "#3b82f6",
        "driver_arrived": "#6366f1",
        "ongoing": "#8b5cf6",
        "completed": "#22c55e",
        "cancelled": "#ef4444",
        "contacted": "#3b82f6",
        "confirmed": "#8b5cf6",
        "paid": "#22c55e",
        "failed": "#ef4444",
        "refunded": "#64748b",
    }

    @admin.display(description="Holat", ordering="status")
    def status_badge(self, obj):
        color = self.COLORS.get(obj.status, "#64748b")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;white-space:nowrap">{}</span>',
            color,
            obj.get_status_display(),
        )


def image_preview(field, width=90):
    """Admin ro'yxatida/sahifasida kichik rasm ko'rsatadi."""
    if not field:
        return format_html('<span style="color:#94a3b8">yo\'q</span>')
    return format_html(
        '<a href="{}" target="_blank">'
        '<img src="{}" style="max-width:{}px;max-height:{}px;'
        'border-radius:6px;border:1px solid #e2e8f0"></a>',
        field.url, field.url, width, width,
    )
