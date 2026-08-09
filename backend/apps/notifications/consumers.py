"""WebSocket ulanishlari.

Ikki kanal:
  ws://.../ws/notifications/?token=<access>  — shaxsiy xabarlar
  ws://.../ws/orders/<id>/?token=<access>    — bitta buyurtmani kuzatish
                                                (status + haydovchi joylashuvi)

Autentifikatsiya query string'dagi JWT orqali: brauzer WebSocket API'si
maxsus header yubora olmaydi, shuning uchun Authorization ishlatilmaydi.
"""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


def user_group(user_id):
    return f"user.{user_id}"


def order_group(order_id):
    return f"order.{order_id}"


#: Barcha onlayn haydovchilar — yangi buyurtma e'loni shu yerga ketadi
DRIVERS_GROUP = "drivers.online"


class BaseAuthConsumer(AsyncJsonWebsocketConsumer):
    """Anonim ulanishni rad etadi."""

    async def connect(self):
        self.user = self.scope.get("user")
        if self.user is None or not getattr(self.user, "is_authenticated", False):
            # 4401 — "unauthorized" uchun odatiy nostandart kod
            await self.close(code=4401)
            return
        await self.on_authenticated()

    async def on_authenticated(self):
        await self.accept()

    async def notify(self, event):
        """Guruhga yuborilgan xabarni klientga uzatadi."""
        await self.send_json(event["data"])


class NotificationConsumer(BaseAuthConsumer):
    """Foydalanuvchining shaxsiy kanali."""

    async def on_authenticated(self):
        self.group = user_group(self.user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)

        # Haydovchi bo'lsa yangi buyurtma e'lonlarini ham oladi
        self.is_driver = await self._is_active_driver()
        if self.is_driver:
            await self.channel_layer.group_add(DRIVERS_GROUP, self.channel_name)

        await self.accept()
        await self.send_json({
            "type": "connected",
            "user_id": self.user.id,
            "unread": await self._unread_count(),
        })

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)
        if getattr(self, "is_driver", False):
            await self.channel_layer.group_discard(DRIVERS_GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Klient faqat 'ping' va 'mark_read' yubora oladi."""
        action = content.get("action")
        if action == "ping":
            await self.send_json({"type": "pong"})
        elif action == "mark_read":
            await self._mark_read(content.get("id"))
            await self.send_json({"type": "marked_read", "id": content.get("id")})

    @database_sync_to_async
    def _is_active_driver(self):
        driver = getattr(self.user, "driver", None)
        return bool(driver and driver.is_active)

    @database_sync_to_async
    def _unread_count(self):
        return self.user.notifications.filter(is_read=False).count()

    @database_sync_to_async
    def _mark_read(self, notification_id):
        if not notification_id:
            return
        self.user.notifications.filter(id=notification_id).update(is_read=True)


class OrderConsumer(BaseAuthConsumer):
    """Bitta buyurtmani real vaqtda kuzatish.

    Faqat mijoz, biriktirilgan haydovchi va admin ulana oladi.
    """

    async def on_authenticated(self):
        self.order_id = int(self.scope["url_route"]["kwargs"]["order_id"])

        if not await self._can_watch():
            await self.close(code=4403)
            return

        self.group = order_group(self.order_id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "order_id": self.order_id})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    @database_sync_to_async
    def _can_watch(self):
        from apps.orders.models import Order

        order = Order.objects.filter(pk=self.order_id).select_related(
            "driver"
        ).first()
        if order is None:
            return False
        if self.user.role == "admin" or self.user.is_staff:
            return True
        if order.client_id == self.user.id:
            return True
        return bool(order.driver and order.driver.user_id == self.user.id)
