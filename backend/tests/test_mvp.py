"""MVP qismi: geocode proxy, WebSocket, bildirishnomalar, naqd to'lov,
yakuniy narx va og'ir texnika narxi.
"""
import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.utils import timezone

from apps.notifications.models import Notification, NotificationType
from apps.notifications.services import DRIVERS_GROUP, notify_user
from apps.orders.models import Order, OrderStatus
from apps.orders.services import change_status
from apps.payments.models import Payment, PaymentState
from apps.requests.services import heavy_equipment_price, wedding_price
from apps.users.serializers import tokens_for_user
from tests.conftest import data_of
from tests.factories import (
    ClientFactory,
    CompletedOrderFactory,
    DriverFactory,
    OrderFactory,
    PaymentFactory,
)


# =====================================================================
# Geocode proxy
# =====================================================================
@pytest.mark.django_db
class TestGeocode:
    def _fake_geocode(self, monkeypatch, natija):
        chaqiruvlar = []

        def fake(address):
            chaqiruvlar.append(address)
            return natija

        monkeypatch.setattr("services.map.map_service.geocode", fake)
        return chaqiruvlar

    def test_manzil_topiladi(self, auth_as, client_user, monkeypatch):
        self._fake_geocode(monkeypatch,
                           {"address": "Chilonzor", "lat": 41.28, "lng": 69.20})
        r = auth_as(client_user).get("/api/geocode/?q=Chilonzor")
        assert r.status_code == 200
        assert data_of(r)["lat"] == 41.28

    def test_natija_keshlanadi(self, auth_as, client_user, monkeypatch):
        cache.clear()
        chaqiruvlar = self._fake_geocode(
            monkeypatch, {"address": "X", "lat": 41.0, "lng": 69.0}
        )
        c = auth_as(client_user)
        c.get("/api/geocode/?q=Yunusobod")
        c.get("/api/geocode/?q=yunusobod")  # katta-kichik harf farq qilmaydi
        assert len(chaqiruvlar) == 1

    def test_topilmasa_404(self, auth_as, client_user, monkeypatch):
        cache.clear()
        self._fake_geocode(monkeypatch, None)
        r = auth_as(client_user).get("/api/geocode/?q=mavjudemasmanzil123")
        assert r.status_code == 404

    @pytest.mark.parametrize("qs", ["", "?q=", "?q=a"])
    def test_notogri_sorov(self, auth_as, client_user, qs):
        assert auth_as(client_user).get(f"/api/geocode/{qs}").status_code == 400

    def test_teskari_geocode(self, auth_as, client_user, monkeypatch):
        cache.clear()
        monkeypatch.setattr("services.map.map_service.reverse_geocode",
                            lambda lat, lng: "Amir Temur ko'chasi 1")
        r = auth_as(client_user).get("/api/geocode/reverse/?lat=41.31&lng=69.24")
        assert r.status_code == 200
        assert data_of(r)["address"] == "Amir Temur ko'chasi 1"

    def test_teskari_notogri_koordinata(self, auth_as, client_user):
        r = auth_as(client_user).get("/api/geocode/reverse/?lat=999&lng=69.24")
        assert r.status_code == 400

    def test_token_talab_qilinadi(self, api):
        """Yandex kaliti himoyalangan bo'lishi kerak."""
        assert api.get("/api/geocode/?q=Chilonzor").status_code == 401


# =====================================================================
# Bildirishnomalar
# =====================================================================
@pytest.mark.django_db
class TestBildirishnomalar:
    def test_status_ozgarganda_mijozga_xabar(self, client_user, driver, tariff):
        o = OrderFactory(client=client_user, tariff=tariff)
        change_status(o, OrderStatus.ACCEPTED, driver=driver)
        n = Notification.objects.filter(user=client_user).first()
        assert n is not None
        assert n.type == NotificationType.ORDER_ACCEPTED
        assert n.payload["order_id"] == o.id

    def test_bekor_qilinganda_haydovchi_ham_xabar_oladi(self, client_user,
                                                        driver, tariff):
        o = OrderFactory(client=client_user, tariff=tariff,
                         status=OrderStatus.ACCEPTED, driver=driver)
        change_status(o, OrderStatus.CANCELLED)
        assert Notification.objects.filter(user=driver.user).exists()
        assert Notification.objects.filter(user=client_user).exists()

    def test_royxat_va_oqilmaganlar_soni(self, auth_as, client_user):
        notify_user(client_user, NotificationType.SYSTEM, "Salom")
        notify_user(client_user, NotificationType.SYSTEM, "Yana")
        d = data_of(auth_as(client_user).get("/api/notifications/"))
        assert d["count"] == 2
        assert d["unread"] == 2

    def test_faqat_ozinikini_koradi(self, auth_as, client_user, other_client):
        notify_user(other_client, NotificationType.SYSTEM, "Begona")
        d = data_of(auth_as(client_user).get("/api/notifications/"))
        assert d["count"] == 0

    def test_oqilgan_deb_belgilash(self, auth_as, client_user):
        n = notify_user(client_user, NotificationType.SYSTEM, "Test")
        r = auth_as(client_user).patch(f"/api/notifications/{n.id}/read/")
        assert r.status_code == 200
        n.refresh_from_db()
        assert n.is_read

    def test_begona_bildirishnomani_belgilab_bolmaydi(self, auth_as,
                                                      client_user, other_client):
        n = notify_user(other_client, NotificationType.SYSTEM, "Begona")
        r = auth_as(client_user).patch(f"/api/notifications/{n.id}/read/")
        assert r.status_code == 404

    def test_hammasini_oqilgan_qilish(self, auth_as, client_user):
        for _ in range(3):
            notify_user(client_user, NotificationType.SYSTEM, "T")
        r = auth_as(client_user).patch("/api/notifications/read-all/")
        assert data_of(r)["marked"] == 3
        assert Notification.objects.filter(user=client_user,
                                           is_read=False).count() == 0

    def test_filtr(self, auth_as, client_user):
        n = notify_user(client_user, NotificationType.SYSTEM, "A")
        notify_user(client_user, NotificationType.SYSTEM, "B")
        Notification.objects.filter(id=n.id).update(is_read=True)
        d = data_of(auth_as(client_user).get("/api/notifications/?is_read=false"))
        assert d["count"] == 1

    def test_token_yoq(self, api):
        assert api.get("/api/notifications/").status_code == 401


# =====================================================================
# WebSocket
# =====================================================================
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebSocket:
    async def _connect(self, path, user=None):
        from config.asgi import application

        token = await database_sync_to_async(
            lambda: tokens_for_user(user)["access_token"]
        )() if user else None
        url = f"{path}?token={token}" if token else path
        comm = WebsocketCommunicator(application, url)
        connected, _ = await comm.connect()
        return comm, connected

    async def test_tokensiz_ulanish_rad_etiladi(self):
        comm, connected = await self._connect("/ws/notifications/")
        assert not connected
        await comm.disconnect()

    async def test_notogri_token_rad_etiladi(self):
        from config.asgi import application

        comm = WebsocketCommunicator(application,
                                     "/ws/notifications/?token=yolgon")
        connected, _ = await comm.connect()
        assert not connected
        await comm.disconnect()

    async def test_ulanish_va_ping(self):
        user = await database_sync_to_async(ClientFactory)()
        comm, connected = await self._connect("/ws/notifications/", user)
        assert connected

        salom = await comm.receive_json_from()
        assert salom["type"] == "connected"
        assert salom["user_id"] == user.id

        await comm.send_json_to({"action": "ping"})
        assert (await comm.receive_json_from())["type"] == "pong"
        await comm.disconnect()

    async def test_xabar_realtime_keladi(self):
        user = await database_sync_to_async(ClientFactory)()
        comm, _ = await self._connect("/ws/notifications/", user)
        await comm.receive_json_from()  # connected

        await database_sync_to_async(notify_user)(
            user, NotificationType.SYSTEM, "Tez xabar", "matn"
        )
        xabar = await comm.receive_json_from()
        assert xabar["type"] == "notification"
        assert xabar["title"] == "Tez xabar"
        await comm.disconnect()

    async def test_buyurtma_kanaliga_begona_ulana_olmaydi(self):
        order = await database_sync_to_async(OrderFactory)()
        begona = await database_sync_to_async(ClientFactory)()
        comm, connected = await self._connect(f"/ws/orders/{order.id}/", begona)
        assert not connected
        await comm.disconnect()

    async def test_buyurtma_egasi_ulanadi(self):
        order = await database_sync_to_async(OrderFactory)()
        egasi = await database_sync_to_async(lambda: order.client)()
        comm, connected = await self._connect(f"/ws/orders/{order.id}/", egasi)
        assert connected
        salom = await comm.receive_json_from()
        assert salom["order_id"] == order.id
        await comm.disconnect()

    async def test_status_ozgarishi_kanalga_keladi(self):
        driver = await database_sync_to_async(DriverFactory)()
        order = await database_sync_to_async(OrderFactory)()
        egasi = await database_sync_to_async(lambda: order.client)()

        comm, _ = await self._connect(f"/ws/orders/{order.id}/", egasi)
        await comm.receive_json_from()  # connected

        await database_sync_to_async(change_status)(
            order, OrderStatus.ACCEPTED, driver=driver
        )
        voqea = await comm.receive_json_from()
        assert voqea["type"] == "order_event"
        assert voqea["status"] == "accepted"
        await comm.disconnect()

    async def test_yangi_buyurtma_haydovchilarga_elon_qilinadi(self):
        layer = get_channel_layer()
        await layer.group_add(DRIVERS_GROUP, "test-channel")

        tariff = await database_sync_to_async(
            lambda: OrderFactory().tariff
        )()
        client = await database_sync_to_async(ClientFactory)()

        from apps.orders.services import create_order

        await database_sync_to_async(create_order)(client, {
            "from_address": "A", "from_lat": 41.28, "from_lng": 69.20,
            "to_address": "B", "to_lat": 41.36, "to_lng": 69.28,
            "tariff_id": tariff.id, "payment_method": "cash",
        })

        xabar = await layer.receive("test-channel")
        assert xabar["data"]["type"] == "new_order"
        assert xabar["data"]["estimated_price"] > 0


# =====================================================================
# Naqd to'lov
# =====================================================================
@pytest.mark.django_db
class TestNaqdTolov:
    def url(self, payment):
        return f"/api/payments/{payment.id}/confirm-cash/"

    def _setup(self, client_user, driver, tariff):
        order = CompletedOrderFactory(client=client_user, driver=driver,
                                      tariff=tariff, payment_method="cash")
        payment = PaymentFactory(order=order, method="cash", amount=30_000)
        return order, payment

    def test_haydovchi_tasdiqlaydi(self, auth_as, client_user, driver, tariff):
        order, payment = self._setup(client_user, driver, tariff)
        r = auth_as(driver.user).patch(self.url(payment))
        assert r.status_code == 200
        payment.refresh_from_db()
        order.refresh_from_db()
        assert payment.status == PaymentState.PAID
        assert order.payment_status == "paid"

    def test_mijozga_xabar_boradi(self, auth_as, client_user, driver, tariff):
        order, payment = self._setup(client_user, driver, tariff)
        auth_as(driver.user).patch(self.url(payment))
        assert Notification.objects.filter(
            user=client_user, type=NotificationType.PAYMENT_PAID
        ).exists()

    def test_mijoz_ozi_tasdiqlay_olmaydi(self, auth_as, client_user, driver,
                                         tariff):
        order, payment = self._setup(client_user, driver, tariff)
        assert auth_as(client_user).patch(self.url(payment)).status_code == 403

    def test_admin_tasdiqlay_oladi(self, auth_as, admin_user, client_user,
                                   driver, tariff):
        order, payment = self._setup(client_user, driver, tariff)
        assert auth_as(admin_user).patch(self.url(payment)).status_code == 200

    def test_yakunlanmagan_safar(self, auth_as, client_user, driver, tariff):
        order = OrderFactory(client=client_user, driver=driver, tariff=tariff,
                             status=OrderStatus.ONGOING, payment_method="cash")
        payment = PaymentFactory(order=order, method="cash")
        assert auth_as(driver.user).patch(self.url(payment)).status_code == 400

    def test_click_tolovida_ishlamaydi(self, auth_as, client_user, driver,
                                       tariff):
        order = CompletedOrderFactory(client=client_user, driver=driver,
                                      tariff=tariff)
        payment = PaymentFactory(order=order, method="click")
        assert auth_as(driver.user).patch(self.url(payment)).status_code == 400

    def test_takroriy_tasdiqlash(self, auth_as, client_user, driver, tariff):
        order, payment = self._setup(client_user, driver, tariff)
        c = auth_as(driver.user)
        assert c.patch(self.url(payment)).status_code == 200
        assert c.patch(self.url(payment)).status_code == 400


# =====================================================================
# Yakuniy narx
# =====================================================================
@pytest.mark.django_db
class TestYakuniyNarx:
    def test_masofa_berilmasa_taxminiy_narx_qoladi(self, driver, tariff):
        o = OrderFactory(status=OrderStatus.ONGOING, driver=driver,
                         tariff=tariff, estimated_price=25_000)
        change_status(o, OrderStatus.COMPLETED)
        o.refresh_from_db()
        assert o.final_price == 25_000

    def test_haqiqiy_masofa_boyicha_qayta_hisoblanadi(self, driver, tariff):
        o = OrderFactory(status=OrderStatus.ONGOING, driver=driver,
                         tariff=tariff, estimated_price=25_000,
                         started_at=timezone.now())
        change_status(o, OrderStatus.COMPLETED, actual_distance_km=20)
        o.refresh_from_db()
        assert o.final_price != 25_000
        assert o.distance_km == 20

    def test_uch_barobardan_oshmaydi(self, driver, tariff):
        """GPS xatosi mijozga zarar qilmasligi kerak."""
        o = OrderFactory(status=OrderStatus.ONGOING, driver=driver,
                         tariff=tariff, estimated_price=10_000,
                         started_at=timezone.now())
        change_status(o, OrderStatus.COMPLETED, actual_distance_km=500)
        o.refresh_from_db()
        assert o.final_price == 30_000

    def test_api_orqali(self, auth_as, driver, tariff):
        o = OrderFactory(status=OrderStatus.ONGOING, driver=driver,
                         tariff=tariff, estimated_price=25_000,
                         started_at=timezone.now())
        r = auth_as(driver.user).patch(
            f"/api/orders/{o.id}/status/",
            {"status": "completed", "actual_distance_km": 12.5},
            format="json",
        )
        assert r.status_code == 200
        o.refresh_from_db()
        assert o.distance_km == 12.5

    def test_notogri_masofa_rad_etiladi(self, auth_as, driver, tariff):
        o = OrderFactory(status=OrderStatus.ONGOING, driver=driver,
                         tariff=tariff)
        r = auth_as(driver.user).patch(
            f"/api/orders/{o.id}/status/",
            {"status": "completed", "actual_distance_km": 99999},
            format="json",
        )
        assert r.status_code == 400


# =====================================================================
# So'rov narxlari
# =====================================================================
@pytest.mark.django_db
class TestSorovNarxlari:
    def test_ogir_texnika_formulasi(self, settings):
        settings.HEAVY_EQUIPMENT_RATES = {"earth": 1_000_000}
        settings.HEAVY_EQUIPMENT_DEFAULT_RATE = 500_000
        narx = heavy_equipment_price(
            "earth", [{"name": "Ekskavator", "quantity": 2}], duration_days=3
        )
        assert narx == 2 * 1_000_000 * 3

    def test_nomalum_kategoriya_sukut_narx(self, settings):
        settings.HEAVY_EQUIPMENT_RATES = {}
        settings.HEAVY_EQUIPMENT_DEFAULT_RATE = 700_000
        assert heavy_equipment_price("kosmik", [{"quantity": 1}]) == 700_000

    def test_bosh_items(self, settings):
        settings.HEAVY_EQUIPMENT_DEFAULT_RATE = 100
        settings.HEAVY_EQUIPMENT_RATES = {}
        assert heavy_equipment_price("earth", []) == 100  # kamida 1 dona

    def test_notogri_quantity_yiqilmaydi(self, settings):
        settings.HEAVY_EQUIPMENT_RATES = {"earth": 100}
        assert heavy_equipment_price("earth", [{"quantity": "ikki"}]) == 100

    def test_api_narx_qaytaradi(self, api):
        r = api.post("/api/heavy-equipment/requests/", {
            "category": "earth",
            "items": [{"name": "Ekskavator", "quantity": 2}],
            "address": "Sergeli", "start_date": "2026-09-01",
            "duration_days": 2, "contact_name": "Olim",
            "contact_phone": "+998901234500",
        }, format="json")
        assert r.status_code == 201
        assert data_of(r)["estimated_price"] > 0

    def test_toy_formulasi(self, settings):
        settings.WEDDING_HOURLY_RATE = 100_000
        assert wedding_price(3, 4) == 1_200_000
