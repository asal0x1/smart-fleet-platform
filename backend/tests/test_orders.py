"""Buyurtma lifecycle: status flow va kim nima qila olishi.

Bu fayl 1-navbatda tuzatilgan eng katta xavfsizlik teshigini qamrab oladi —
ilgari istalgan foydalanuvchi begona buyurtma statusini o'zgartira olardi.
"""
import pytest
from rest_framework.exceptions import ValidationError

from apps.drivers.models import Driver
from apps.orders.models import Order, OrderStatus
from apps.orders.services import STATUS_FLOW, change_status
from tests.conftest import data_of
from tests.factories import DriverFactory, OrderFactory

pytestmark = pytest.mark.django_db


def status_url(order):
    return f"/api/orders/{order.id}/status/"


# =====================================================================
# Servis darajasidagi status flow
# =====================================================================
class TestStatusFlowServis:
    @pytest.mark.parametrize("frm,to", [
        (OrderStatus.PENDING, OrderStatus.ACCEPTED),
        (OrderStatus.PENDING, OrderStatus.CANCELLED),
        (OrderStatus.ACCEPTED, OrderStatus.DRIVER_ARRIVED),
        (OrderStatus.DRIVER_ARRIVED, OrderStatus.ONGOING),
        (OrderStatus.ONGOING, OrderStatus.COMPLETED),
        (OrderStatus.ONGOING, OrderStatus.CANCELLED),
    ])
    def test_ruxsat_etilgan_otishlar(self, frm, to, driver):
        order = OrderFactory(status=frm, driver=None if frm == OrderStatus.PENDING else driver)
        change_status(order, to, driver=driver if to == OrderStatus.ACCEPTED else None)
        order.refresh_from_db()
        assert order.status == to

    @pytest.mark.parametrize("frm,to", [
        (OrderStatus.PENDING, OrderStatus.ONGOING),
        (OrderStatus.PENDING, OrderStatus.COMPLETED),
        (OrderStatus.ACCEPTED, OrderStatus.COMPLETED),
        (OrderStatus.COMPLETED, OrderStatus.ONGOING),
        (OrderStatus.COMPLETED, OrderStatus.CANCELLED),
        (OrderStatus.CANCELLED, OrderStatus.ACCEPTED),
    ])
    def test_taqiqlangan_otishlar(self, frm, to, driver):
        order = OrderFactory(status=frm, driver=driver)
        with pytest.raises(ValidationError):
            change_status(order, to, driver=driver)

    def test_yakuniy_holatlardan_chiqib_bolmaydi(self):
        assert STATUS_FLOW[OrderStatus.COMPLETED] == []
        assert STATUS_FLOW[OrderStatus.CANCELLED] == []

    def test_accepted_haydovchisiz_bolmaydi(self):
        order = OrderFactory(status=OrderStatus.PENDING)
        with pytest.raises(ValidationError):
            change_status(order, OrderStatus.ACCEPTED, driver=None)

    def test_completed_safarlar_sonini_oshiradi(self, driver):
        order = OrderFactory(status=OrderStatus.ONGOING, driver=driver)
        oldin = driver.total_trips
        change_status(order, OrderStatus.COMPLETED)
        driver.refresh_from_db()
        assert driver.total_trips == oldin + 1

    def test_completed_sanalarni_toldiradi(self, driver):
        order = OrderFactory(status=OrderStatus.ONGOING, driver=driver)
        change_status(order, OrderStatus.COMPLETED)
        order.refresh_from_db()
        assert order.completed_at is not None
        assert order.final_price == order.estimated_price


# =====================================================================
# Buyurtma yaratish
# =====================================================================
class TestBuyurtmaYaratish:
    def _payload(self, tariff):
        return {
            "from_address": "Chilonzor", "from_lat": 41.2856, "from_lng": 69.2034,
            "to_address": "Yunusobod", "to_lat": 41.3600, "to_lng": 69.2890,
            "tariff_id": tariff.id, "payment_method": "cash",
        }

    def test_mijoz_yaratadi(self, auth_as, client_user, tariff):
        r = auth_as(client_user).post("/api/orders/", self._payload(tariff),
                                      format="json")
        assert r.status_code == 201
        assert Order.objects.filter(client=client_user).count() == 1
        assert data_of(r)["estimated_price"] > 0

    def test_haydovchi_yarata_olmaydi(self, auth_as, driver, tariff):
        r = auth_as(driver.user).post("/api/orders/", self._payload(tariff),
                                      format="json")
        assert r.status_code == 403
        assert Order.objects.count() == 0

    def test_notogri_koordinata(self, auth_as, client_user, tariff):
        p = self._payload(tariff)
        p["from_lat"] = 91
        r = auth_as(client_user).post("/api/orders/", p, format="json")
        assert r.status_code == 400

    def test_mavjud_bolmagan_tarif(self, auth_as, client_user, tariff):
        p = self._payload(tariff)
        p["tariff_id"] = 999999
        r = auth_as(client_user).post("/api/orders/", p, format="json")
        assert r.status_code == 400

    def test_ochirilgan_tarif(self, auth_as, client_user, tariff):
        tariff.is_active = False
        tariff.save()
        r = auth_as(client_user).post("/api/orders/", self._payload(tariff),
                                      format="json")
        assert r.status_code == 400

    def test_token_yoq(self, api, tariff):
        assert api.post("/api/orders/", self._payload(tariff),
                        format="json").status_code == 401


# =====================================================================
# Status o'zgartirish — ruxsatlar (ENG MUHIM QISM)
# =====================================================================
class TestStatusRuxsatlari:
    def test_begona_mijoz_bekor_qila_olmaydi(self, auth_as, order, other_client):
        r = auth_as(other_client).patch(status_url(order),
                                        {"status": "cancelled"}, format="json")
        assert r.status_code == 403
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING

    def test_egasi_bekor_qila_oladi(self, auth_as, order, client_user):
        r = auth_as(client_user).patch(status_url(order),
                                       {"status": "cancelled"}, format="json")
        assert r.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_admin_bekor_qila_oladi(self, auth_as, order, admin_user):
        r = auth_as(admin_user).patch(status_url(order),
                                      {"status": "cancelled"}, format="json")
        assert r.status_code == 200

    def test_mijoz_accepted_yubora_olmaydi(self, auth_as, order, other_client):
        r = auth_as(other_client).patch(status_url(order),
                                        {"status": "accepted"}, format="json")
        assert r.status_code == 403

    def test_mijozga_driver_obyekti_yaratilmaydi(self, auth_as, order, other_client):
        """Ilgari get_or_create_driver mijozni haydovchiga aylantirib qo'yardi."""
        oldin = Driver.objects.count()
        auth_as(other_client).patch(status_url(order),
                                    {"status": "accepted"}, format="json")
        assert Driver.objects.count() == oldin
        assert not Driver.objects.filter(user=other_client).exists()

    def test_tasdiqlanmagan_haydovchi_qabul_qila_olmaydi(
        self, auth_as, order, unapproved_driver
    ):
        r = auth_as(unapproved_driver.user).patch(status_url(order),
                                                  {"status": "accepted"},
                                                  format="json")
        assert r.status_code == 403
        order.refresh_from_db()
        assert order.driver is None

    def test_tasdiqlangan_haydovchi_qabul_qiladi(self, auth_as, order, driver):
        r = auth_as(driver.user).patch(status_url(order),
                                       {"status": "accepted"}, format="json")
        assert r.status_code == 200
        order.refresh_from_db()
        assert order.driver_id == driver.id
        assert order.accepted_at is not None

    def test_band_buyurtmani_ikkinchi_haydovchi_ololmaydi(
        self, auth_as, order, driver, driver2
    ):
        auth_as(driver.user).patch(status_url(order),
                                   {"status": "accepted"}, format="json")
        r = auth_as(driver2.user).patch(status_url(order),
                                        {"status": "accepted"}, format="json")
        assert r.status_code == 409
        order.refresh_from_db()
        assert order.driver_id == driver.id

    def test_biriktirilmagan_haydovchi_statusni_ozgartira_olmaydi(
        self, auth_as, driver, driver2
    ):
        order = OrderFactory(status=OrderStatus.ACCEPTED, driver=driver)
        r = auth_as(driver2.user).patch(status_url(order),
                                        {"status": "driver_arrived"}, format="json")
        assert r.status_code == 403

    def test_biriktirilgan_haydovchi_ozgartiradi(self, auth_as, driver):
        order = OrderFactory(status=OrderStatus.ACCEPTED, driver=driver)
        r = auth_as(driver.user).patch(status_url(order),
                                       {"status": "driver_arrived"}, format="json")
        assert r.status_code == 200

    def test_mijoz_safarni_yakunlay_olmaydi(self, auth_as, client_user, driver):
        order = OrderFactory(status=OrderStatus.ONGOING, client=client_user,
                             driver=driver)
        r = auth_as(client_user).patch(status_url(order),
                                       {"status": "completed"}, format="json")
        assert r.status_code == 403

    def test_admin_accepted_yubora_olmaydi(self, auth_as, order, admin_user):
        """Admin uchun alohida assign/ endpointi bor."""
        r = auth_as(admin_user).patch(status_url(order),
                                      {"status": "accepted"}, format="json")
        assert r.status_code == 400

    def test_notogri_status_qiymati(self, auth_as, order, client_user):
        r = auth_as(client_user).patch(status_url(order),
                                       {"status": "kosmosda"}, format="json")
        assert r.status_code == 400

    def test_mavjud_bolmagan_buyurtma(self, auth_as, client_user):
        r = auth_as(client_user).patch("/api/orders/999999/status/",
                                       {"status": "cancelled"}, format="json")
        assert r.status_code == 404

    def test_token_yoq(self, api, order):
        assert api.patch(status_url(order), {"status": "cancelled"},
                         format="json").status_code == 401


# =====================================================================
# Ro'yxat va detal
# =====================================================================
class TestBuyurtmalarRoyxati:
    def test_mijoz_faqat_ozinikini_koradi(self, auth_as, client_user, other_client):
        OrderFactory(client=client_user)
        OrderFactory(client=other_client)
        r = auth_as(client_user).get("/api/orders/")
        assert len(data_of(r)) == 1

    def test_haydovchi_faqat_ozining_safarlarini_koradi(self, auth_as, driver, driver2):
        OrderFactory(driver=driver, status=OrderStatus.ACCEPTED)
        OrderFactory(driver=driver2, status=OrderStatus.ACCEPTED)
        r = auth_as(driver.user).get("/api/orders/")
        assert len(data_of(r)) == 1

    def test_admin_hammasini_koradi(self, auth_as, admin_user):
        OrderFactory()
        OrderFactory()
        r = auth_as(admin_user).get("/api/orders/")
        assert len(data_of(r)) == 2

    def test_status_boyicha_filtr(self, auth_as, client_user, driver):
        OrderFactory(client=client_user, status=OrderStatus.PENDING)
        OrderFactory(client=client_user, status=OrderStatus.COMPLETED, driver=driver)
        r = auth_as(client_user).get("/api/orders/?status=completed")
        assert len(data_of(r)) == 1

    def test_detal_begonaga_berilmaydi(self, auth_as, order, other_client):
        r = auth_as(other_client).get(f"/api/orders/{order.id}/")
        assert r.status_code == 403

    def test_detal_egasiga_beriladi(self, auth_as, order, client_user):
        r = auth_as(client_user).get(f"/api/orders/{order.id}/")
        assert r.status_code == 200

    def test_detal_biriktirilgan_haydovchiga_beriladi(self, auth_as, driver):
        order = OrderFactory(status=OrderStatus.ACCEPTED, driver=driver)
        assert auth_as(driver.user).get(f"/api/orders/{order.id}/").status_code == 200


class TestOchiqBuyurtmalar:
    def test_tasdiqlangan_haydovchi_koradi(self, auth_as, driver):
        OrderFactory(status=OrderStatus.PENDING)
        r = auth_as(driver.user).get("/api/orders/available/")
        assert r.status_code == 200
        assert len(data_of(r)) == 1

    def test_tasdiqlanmagan_haydovchi_kormaydi(self, auth_as, unapproved_driver):
        OrderFactory(status=OrderStatus.PENDING)
        r = auth_as(unapproved_driver.user).get("/api/orders/available/")
        assert len(data_of(r)) == 0

    def test_band_buyurtma_royxatda_yoq(self, auth_as, driver, driver2):
        OrderFactory(status=OrderStatus.ACCEPTED, driver=driver2)
        r = auth_as(driver.user).get("/api/orders/available/")
        assert len(data_of(r)) == 0

    def test_mijoz_kira_olmaydi(self, auth_as, client_user):
        assert auth_as(client_user).get("/api/orders/available/").status_code == 403


class TestJavobFormati:
    """Barcha endpointlar bir xil konvertda javob qaytarishi kerak."""

    def test_tariflar_konvertda(self, auth_as, client_user, tariff):
        body = auth_as(client_user).get("/api/orders/tariffs/").json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    def test_ochiq_buyurtmalar_konvertda(self, auth_as, driver):
        body = auth_as(driver.user).get("/api/orders/available/").json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
