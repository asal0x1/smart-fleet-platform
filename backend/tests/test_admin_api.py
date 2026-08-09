"""Admin API — ruxsatlar, filtrlar, action'lar."""
import pytest

from apps.drivers.models import Driver
from apps.orders.models import Order, OrderStatus, Tariff
from apps.payments.models import PaymentState
from apps.requests.models import HeavyEquipmentRequest, WeddingRequest
from tests.conftest import data_of
from tests.factories import (
    ClientFactory,
    CompletedOrderFactory,
    HeavyRequestFactory,
    OrderFactory,
    PaymentFactory,
    UnapprovedDriverFactory,
    WeddingRequestFactory,
)

pytestmark = pytest.mark.django_db

ENDPOINTS = [
    "/api/admin/stats/",
    "/api/admin/stats/revenue/",
    "/api/admin/users/",
    "/api/admin/drivers/",
    "/api/admin/orders/",
    "/api/admin/tariffs/",
    "/api/admin/payments/",
    "/api/admin/requests/heavy/",
    "/api/admin/requests/wedding/",
]


class TestRuxsatlar:
    @pytest.mark.parametrize("url", ENDPOINTS)
    def test_anonim_401(self, api, url):
        assert api.get(url).status_code == 401

    @pytest.mark.parametrize("url", ENDPOINTS)
    def test_mijoz_403(self, auth_as, client_user, url):
        assert auth_as(client_user).get(url).status_code == 403

    @pytest.mark.parametrize("url", ENDPOINTS)
    def test_haydovchi_403(self, auth_as, driver, url):
        assert auth_as(driver.user).get(url).status_code == 403

    @pytest.mark.parametrize("url", ENDPOINTS)
    def test_admin_200(self, auth_as, admin_user, url):
        assert auth_as(admin_user).get(url).status_code == 200

    def test_staff_ham_kira_oladi(self, auth_as, url=None):
        staff = ClientFactory(is_staff=True)
        assert auth_as(staff).get("/api/admin/stats/").status_code == 200


class TestStatistika:
    def test_dashboard_bloklari(self, auth_as, admin_user, driver, tariff):
        CompletedOrderFactory(tariff=tariff, final_price=50_000)
        OrderFactory(tariff=tariff)
        d = data_of(auth_as(admin_user).get("/api/admin/stats/"))
        assert set(d) == {"users", "drivers", "orders", "revenue", "requests"}
        assert d["orders"]["total"] == 2
        assert d["revenue"]["total"] == 50_000

    def test_revenue_seriyasi(self, auth_as, admin_user, tariff):
        CompletedOrderFactory(tariff=tariff, final_price=30_000)
        d = data_of(auth_as(admin_user).get(
            "/api/admin/stats/revenue/?from=2020-01-01&to=2030-01-01&group_by=month"
        ))
        assert d["total_revenue"] == 30_000
        assert len(d["series"]) >= 1

    def test_notogri_group_by(self, auth_as, admin_user):
        r = auth_as(admin_user).get("/api/admin/stats/revenue/?group_by=asr")
        assert r.status_code == 400

    def test_notogri_sana_formati(self, auth_as, admin_user):
        r = auth_as(admin_user).get("/api/admin/stats/revenue/?from=06.08.2026")
        assert r.status_code == 400

    def test_teskari_sana_oraligi(self, auth_as, admin_user):
        r = auth_as(admin_user).get(
            "/api/admin/stats/revenue/?from=2026-12-01&to=2026-01-01"
        )
        assert r.status_code == 400


class TestFoydalanuvchilar:
    def test_royxat_paginatsiyasi(self, auth_as, admin_user):
        ClientFactory.create_batch(3)
        d = data_of(auth_as(admin_user).get("/api/admin/users/"))
        assert d["count"] == 4  # 3 + admin
        assert "results" in d and "total_pages" in d

    def test_rol_boyicha_filtr(self, auth_as, admin_user, driver):
        d = data_of(auth_as(admin_user).get("/api/admin/users/?role=driver"))
        assert d["count"] == 1

    def test_qidiruv(self, auth_as, admin_user):
        ClientFactory(full_name="Zafar Alimov")
        d = data_of(auth_as(admin_user).get("/api/admin/users/?search=Zafar"))
        assert d["count"] == 1

    def test_detal_oxirgi_buyurtmalar_bilan(self, auth_as, admin_user, client_user,
                                            tariff):
        OrderFactory(client=client_user, tariff=tariff)
        d = data_of(auth_as(admin_user).get(f"/api/admin/users/{client_user.id}/"))
        assert d["user"]["id"] == client_user.id
        assert len(d["last_orders"]) == 1

    def test_bloklash(self, auth_as, admin_user, client_user):
        r = auth_as(admin_user).patch(f"/api/admin/users/{client_user.id}/block/",
                                      {"is_active": False}, format="json")
        assert r.status_code == 200
        client_user.refresh_from_db()
        assert not client_user.is_active

    def test_ozini_bloklab_bolmaydi(self, auth_as, admin_user):
        r = auth_as(admin_user).patch(f"/api/admin/users/{admin_user.id}/block/",
                                      {"is_active": False}, format="json")
        assert r.status_code == 400

    def test_superuserni_bloklab_bolmaydi(self, auth_as, admin_user):
        su = ClientFactory(is_superuser=True)
        r = auth_as(admin_user).patch(f"/api/admin/users/{su.id}/block/",
                                      {"is_active": False}, format="json")
        assert r.status_code == 403

    def test_mavjud_bolmagan_user(self, auth_as, admin_user):
        r = auth_as(admin_user).get("/api/admin/users/999999/")
        assert r.status_code == 404


class TestHaydovchilar:
    def test_tasdiqlanmaganlar_filtri(self, auth_as, admin_user, driver):
        UnapprovedDriverFactory()
        d = data_of(auth_as(admin_user).get("/api/admin/drivers/?is_active=false"))
        assert d["count"] == 1

    def test_tasdiqlash(self, auth_as, admin_user, unapproved_driver):
        r = auth_as(admin_user).patch(
            f"/api/admin/drivers/{unapproved_driver.id}/approve/", {}, format="json"
        )
        assert r.status_code == 200
        unapproved_driver.refresh_from_db()
        assert unapproved_driver.is_active

    def test_mashina_raqamisiz_tasdiqlab_bolmaydi(self, auth_as, admin_user):
        drv = UnapprovedDriverFactory(car_number="")
        r = auth_as(admin_user).patch(f"/api/admin/drivers/{drv.id}/approve/",
                                      {}, format="json")
        assert r.status_code == 400

    def test_tasdiq_bekor_qilinsa_offline_boladi(self, auth_as, admin_user, driver):
        auth_as(admin_user).patch(f"/api/admin/drivers/{driver.id}/approve/",
                                  {"is_active": False}, format="json")
        driver.refresh_from_db()
        assert not driver.is_active and not driver.is_online

    def test_bloklash_user_hisobini_ochiradi(self, auth_as, admin_user, driver):
        auth_as(admin_user).patch(f"/api/admin/drivers/{driver.id}/block/",
                                  {"is_active": False}, format="json")
        driver.refresh_from_db()
        driver.user.refresh_from_db()
        assert not driver.user.is_active
        assert not driver.is_online

    def test_detal_daromad_bilan(self, auth_as, admin_user, driver, tariff):
        CompletedOrderFactory(driver=driver, tariff=tariff, final_price=40_000)
        d = data_of(auth_as(admin_user).get(f"/api/admin/drivers/{driver.id}/"))
        assert d["earnings"]["total"] == 40_000
        assert d["earnings"]["completed_trips"] == 1

    def test_tahrirlash(self, auth_as, admin_user, driver):
        r = auth_as(admin_user).patch(f"/api/admin/drivers/{driver.id}/",
                                      {"car_color": "qora"}, format="json")
        assert r.status_code == 200
        driver.refresh_from_db()
        assert driver.car_color == "qora"


class TestBuyurtmalar:
    def test_status_filtri(self, auth_as, admin_user, tariff):
        OrderFactory(tariff=tariff)
        CompletedOrderFactory(tariff=tariff)
        d = data_of(auth_as(admin_user).get("/api/admin/orders/?status=pending"))
        assert d["count"] == 1

    def test_haydovchisiz_filtri(self, auth_as, admin_user, tariff):
        OrderFactory(tariff=tariff)
        CompletedOrderFactory(tariff=tariff)
        d = data_of(auth_as(admin_user).get("/api/admin/orders/?no_driver=true"))
        assert d["count"] == 1

    def test_bekor_qilish_sabab_bilan(self, auth_as, admin_user, order):
        r = auth_as(admin_user).patch(f"/api/admin/orders/{order.id}/cancel/",
                                      {"reason": "Mijoz javob bermadi"},
                                      format="json")
        assert r.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED
        assert order.cancel_reason == "Mijoz javob bermadi"

    def test_yakunlangan_buyurtmani_bekor_qilib_bolmaydi(self, auth_as, admin_user,
                                                         tariff):
        o = CompletedOrderFactory(tariff=tariff)
        r = auth_as(admin_user).patch(f"/api/admin/orders/{o.id}/cancel/",
                                      {}, format="json")
        assert r.status_code == 400

    def test_bekor_qilinganda_kutilayotgan_tolov_ham_bekor(self, auth_as,
                                                           admin_user, order):
        p = PaymentFactory(order=order)
        auth_as(admin_user).patch(f"/api/admin/orders/{order.id}/cancel/",
                                  {}, format="json")
        p.refresh_from_db()
        assert p.status == PaymentState.CANCELLED

    def test_haydovchi_biriktirish(self, auth_as, admin_user, order, driver):
        r = auth_as(admin_user).patch(f"/api/admin/orders/{order.id}/assign/",
                                      {"driver_id": driver.id}, format="json")
        assert r.status_code == 200
        order.refresh_from_db()
        assert order.driver_id == driver.id
        assert order.status == OrderStatus.ACCEPTED

    def test_tasdiqlanmagan_haydovchini_biriktirib_bolmaydi(self, auth_as,
                                                            admin_user, order,
                                                            unapproved_driver):
        r = auth_as(admin_user).patch(f"/api/admin/orders/{order.id}/assign/",
                                      {"driver_id": unapproved_driver.id},
                                      format="json")
        assert r.status_code == 400

    def test_detal_tolovlar_bilan(self, auth_as, admin_user, order):
        PaymentFactory(order=order)
        d = data_of(auth_as(admin_user).get(f"/api/admin/orders/{order.id}/"))
        assert d["order"]["id"] == order.id
        assert len(d["payments"]) == 1


class TestTariflar:
    def test_yaratish(self, auth_as, admin_user):
        r = auth_as(admin_user).post("/api/admin/tariffs/", {
            "name": "Yangi", "base_fare": 6000, "per_km": 1800,
            "per_minute": 400, "minimum_fare": 12000,
        }, format="json")
        assert r.status_code == 201
        assert Tariff.objects.filter(name="Yangi").exists()

    def test_minimal_narx_validatsiyasi(self, auth_as, admin_user):
        r = auth_as(admin_user).post("/api/admin/tariffs/", {
            "name": "X", "base_fare": 10000, "per_km": 100,
            "per_minute": 100, "minimum_fare": 5000,
        }, format="json")
        assert r.status_code == 400

    def test_tahrirlash(self, auth_as, admin_user, tariff):
        r = auth_as(admin_user).patch(f"/api/admin/tariffs/{tariff.id}/",
                                      {"per_km": 3000}, format="json")
        assert r.status_code == 200
        tariff.refresh_from_db()
        assert tariff.per_km == 3000

    def test_ishlatilmagan_tarif_ochiriladi(self, auth_as, admin_user, tariff):
        r = auth_as(admin_user).delete(f"/api/admin/tariffs/{tariff.id}/")
        assert r.status_code == 200
        assert not Tariff.objects.filter(id=tariff.id).exists()

    def test_ishlatilgan_tarif_ochirilmaydi_faqat_ochib_qoyiladi(self, auth_as,
                                                                 admin_user,
                                                                 tariff):
        OrderFactory(tariff=tariff)
        r = auth_as(admin_user).delete(f"/api/admin/tariffs/{tariff.id}/")
        assert r.status_code == 200
        tariff.refresh_from_db()
        assert not tariff.is_active


class TestTolovlar:
    def test_summary_filtrga_mos_keladi(self, auth_as, admin_user, tariff):
        PaymentFactory(order=OrderFactory(tariff=tariff), amount=10_000,
                       status=PaymentState.PAID)
        PaymentFactory(order=OrderFactory(tariff=tariff), amount=5_000,
                       status=PaymentState.PENDING)
        d = data_of(auth_as(admin_user).get("/api/admin/payments/"))
        assert d["summary"]["paid_amount"] == 10_000
        assert d["summary"]["total_amount"] == 15_000

    def test_status_filtri(self, auth_as, admin_user, tariff):
        PaymentFactory(order=OrderFactory(tariff=tariff), status=PaymentState.PAID)
        PaymentFactory(order=OrderFactory(tariff=tariff))
        d = data_of(auth_as(admin_user).get("/api/admin/payments/?status=paid"))
        assert d["count"] == 1


class TestSorovlar:
    def test_ogir_texnika_royxati(self, auth_as, admin_user):
        HeavyRequestFactory.create_batch(2)
        d = data_of(auth_as(admin_user).get("/api/admin/requests/heavy/"))
        assert d["count"] == 2

    def test_status_ozgartirish(self, auth_as, admin_user):
        req = HeavyRequestFactory()
        r = auth_as(admin_user).patch(
            f"/api/admin/requests/heavy/{req.id}/status/",
            {"status": "contacted", "notes": "Qo'ng'iroq qilindi"}, format="json"
        )
        assert r.status_code == 200
        req.refresh_from_db()
        assert req.status == "contacted"
        assert "Qo'ng'iroq qilindi" in req.notes

    def test_izohlar_ustiga_qoshiladi_ochirilmaydi(self, auth_as, admin_user):
        req = HeavyRequestFactory(notes="Boshlangich izoh")
        auth_as(admin_user).patch(f"/api/admin/requests/heavy/{req.id}/status/",
                                  {"status": "contacted", "notes": "Ikkinchi"},
                                  format="json")
        req.refresh_from_db()
        assert "Boshlangich izoh" in req.notes and "Ikkinchi" in req.notes

    def test_notogri_status(self, auth_as, admin_user):
        req = HeavyRequestFactory()
        r = auth_as(admin_user).patch(f"/api/admin/requests/heavy/{req.id}/status/",
                                      {"status": "kosmosda"}, format="json")
        assert r.status_code == 400

    def test_toy_sorovi_ochirish(self, auth_as, admin_user):
        req = WeddingRequestFactory()
        r = auth_as(admin_user).delete(f"/api/admin/requests/wedding/{req.id}/")
        assert r.status_code == 200
        assert not WeddingRequest.objects.filter(id=req.id).exists()

    def test_toy_sorovi_status_filtri(self, auth_as, admin_user):
        WeddingRequestFactory(status="confirmed")
        WeddingRequestFactory()
        d = data_of(auth_as(admin_user).get(
            "/api/admin/requests/wedding/?status=pending"
        ))
        assert d["count"] == 1
