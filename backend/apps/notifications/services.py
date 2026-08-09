"""Bildirishnoma yuborish — WebSocket + bazaga saqlash.

Bu modul view'lar va servislardan chaqiriladi. WebSocket ishlamay qolsa
ham asosiy oqim buzilmasligi kerak, shuning uchun barcha yuborishlar
xatolarni yutadi va faqat log qoldiradi.
"""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .consumers import DRIVERS_GROUP, order_group, user_group
from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


def _send_to_group(group, payload):
    """Guruhga xabar yuboradi. Channel layer yo'q bo'lsa jim o'tadi."""
    layer = get_channel_layer()
    if layer is None:
        return False
    try:
        async_to_sync(layer.group_send)(group, {"type": "notify", "data": payload})
        return True
    except Exception as exc:  # noqa: BLE001 — WS xatosi oqimni buzmasligi kerak
        logger.warning("WebSocket yuborishda xato (%s): %s", group, exc)
        return False


def notify_user(user, type_, title, body="", payload=None, save=True):
    """Bitta foydalanuvchiga xabar: bazaga yozadi va WS orqali yuboradi."""
    payload = payload or {}
    notification = None

    if save:
        notification = Notification.objects.create(
            user=user, type=type_, title=title, body=body, payload=payload
        )

    _send_to_group(user_group(user.id), {
        "type": "notification",
        "id": notification.id if notification else None,
        "notification_type": type_,
        "title": title,
        "body": body,
        "payload": payload,
    })
    return notification


def broadcast_order_event(order, event, extra=None):
    """Buyurtma kanaliga voqea yuboradi (mijoz + haydovchi + admin ko'radi)."""
    data = {
        "type": "order_event",
        "event": event,
        "order_id": order.id,
        "status": order.status,
    }
    if extra:
        data.update(extra)
    _send_to_group(order_group(order.id), data)


def broadcast_new_order(order, distance_km=None):
    """Onlayn haydovchilarga yangi buyurtma e'loni.

    Bitta buyurtma hamma tasdiqlangan haydovchiga ketadi; kim birinchi
    qabul qilsa, o'shanikiga o'tadi (ChangeStatusView da qulflangan).
    """
    _send_to_group(DRIVERS_GROUP, {
        "type": "new_order",
        "order_id": order.id,
        "from_address": order.from_address,
        "to_address": order.to_address,
        "estimated_price": order.estimated_price,
        "distance_km": order.distance_km,
        "tariff": order.tariff.name if order.tariff_id else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    })


def broadcast_driver_location(order, lat, lng):
    """Haydovchi joylashuvini buyurtma kanaliga uzatadi.

    Bazaga saqlanmaydi — bu sekundiga bir marta keladigan oqim.
    """
    _send_to_group(order_group(order.id), {
        "type": "driver_location",
        "order_id": order.id,
        "lat": lat,
        "lng": lng,
    })


# ---------------------------------------------------------------------
# Status o'zgarishlariga tayyor xabarlar
# ---------------------------------------------------------------------
STATUS_MESSAGES = {
    "accepted": (
        NotificationType.ORDER_ACCEPTED,
        "Haydovchi topildi",
        "Haydovchi buyurtmangizni qabul qildi va yo'lga chiqdi",
    ),
    "driver_arrived": (
        NotificationType.DRIVER_ARRIVED,
        "Haydovchi yetib keldi",
        "Haydovchi belgilangan manzilda kutmoqda",
    ),
    "ongoing": (
        NotificationType.ORDER_STARTED,
        "Safar boshlandi",
        "Xayrli yo'l!",
    ),
    "completed": (
        NotificationType.ORDER_COMPLETED,
        "Safar yakunlandi",
        "Haydovchini baholashni unutmang",
    ),
    "cancelled": (
        NotificationType.ORDER_CANCELLED,
        "Buyurtma bekor qilindi",
        "",
    ),
}


def notify_order_status(order):
    """Status o'zgargach mijoz va haydovchiga xabar beradi."""
    broadcast_order_event(order, f"status.{order.status}")

    xabar = STATUS_MESSAGES.get(order.status)
    if xabar is None:
        return

    type_, title, body = xabar
    payload = {"order_id": order.id, "status": order.status}

    # Mijoz har doim xabardor bo'ladi
    if order.client_id:
        notify_user(order.client, type_, title, body, payload)

    # Haydovchiga faqat bekor qilinganini aytish kifoya —
    # qolgan o'zgarishlarni o'zi qilyapti
    if order.status == "cancelled" and order.driver_id:
        notify_user(
            order.driver.user, type_, "Buyurtma bekor qilindi",
            f"#{order.id} buyurtma bekor qilindi", payload,
        )
