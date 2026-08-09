"""3-navbat: hujjat/avatar yuklash, sharh va reyting, masofa filtri."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.drivers.models import Driver
from apps.orders.models import Order, OrderStatus, Review, ReviewKind
from apps.orders.services import recalculate_driver_rating
from tests.conftest import data_of
from tests.factories import (
    ClientFactory,
    CompletedOrderFactory,
    DriverFactory,
    NoDocsDriverFactory,
    OrderFactory,
    ReviewFactory,
    UnapprovedDriverFactory,
    point,
)

pytestmark = pytest.mark.django_db


def make_image(name="test.jpg", size=(20, 20), fmt="JPEG", raw_bytes=None):
    """Haqiqiy rasm fayli — ImageField validatsiyasidan o'tadi."""
    if raw_bytes is not None:
        return SimpleUploadedFile(name, raw_bytes, content_type="image/jpeg")
    buf = io.BytesIO()
    Image.new("RGB", size, (100, 150, 200)).save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type=f"image/{fmt.lower()}")


# =====================================================================
# Hujjat yuklash
# =====================================================================
class TestHujjatYuklash:
    URL = "/api/drivers/documents/"

    def test_yuklash(self, auth_as):
        d = NoDocsDriverFactory()
        r = auth_as(d.user).post(self.URL, {
            "license_photo": make_image("license.jpg"),
            "tech_passport_photo": make_image("techpass.jpg"),
        }, format="multipart")
        assert r.status_code == 200
        d.refresh_from_db()
        assert d.license_photo and d.tech_passport_photo
        assert d.has_documents

    def test_yetishmayotgan_hujjatlar_korsatiladi(self, auth_as):
        d = NoDocsDriverFactory()
        r = auth_as(d.user).post(self.URL, {
            "license_photo": make_image(),
        }, format="multipart")
        assert r.status_code == 200
        yetishmayotgan = data_of(r)["missing_documents"]
        assert "Texnik pasport" in yetishmayotgan
        assert data_of(r)["is_complete"] is False

    def test_bosh_sorov_rad_etiladi(self, auth_as):
        d = NoDocsDriverFactory()
        r = auth_as(d.user).post(self.URL, {}, format="multipart")
        assert r.status_code == 400

    def test_katta_fayl_rad_etiladi(self, auth_as):
        d = NoDocsDriverFactory()
        katta = make_image("big.jpg", raw_bytes=b"x" * (6 * 1024 * 1024))
        r = auth_as(d.user).post(self.URL, {"license_photo": katta},
                                 format="multipart")
        assert r.status_code == 400

    def test_notogri_format(self, auth_as):
        d = NoDocsDriverFactory()
        pdf = SimpleUploadedFile("hujjat.pdf", b"%PDF-1.4 fake",
                                 content_type="application/pdf")
        r = auth_as(d.user).post(self.URL, {"license_photo": pdf},
                                 format="multipart")
        assert r.status_code == 400

    def test_mijoz_yuklay_olmaydi(self, auth_as, client_user):
        r = auth_as(client_user).post(self.URL,
                                      {"license_photo": make_image()},
                                      format="multipart")
        assert r.status_code == 403

    def test_hujjat_ochirilsa_tasdiq_bekor_boladi(self, auth_as):
        """Tasdiqlangan haydovchi hujjatini o'zgartirsa qayta tekshirish kerak."""
        d = DriverFactory(is_active=True)
        d.tech_passport_photo = None
        d.save()
        auth_as(d.user).post(self.URL, {"car_photo": make_image()},
                             format="multipart")
        d.refresh_from_db()
        assert not d.is_active

    def test_profilda_hujjat_holati_korinadi(self, auth_as):
        d = NoDocsDriverFactory()
        r = auth_as(d.user).get("/api/drivers/profile/")
        assert data_of(r)["documents_complete"] is False
        assert len(data_of(r)["missing_documents"]) == 2

    def test_token_yoq(self, api):
        assert api.post(self.URL, {}, format="multipart").status_code == 401


class TestAvatarYuklash:
    def test_yuklash(self, auth_as, client_user):
        r = auth_as(client_user).patch("/api/auth/profile/",
                                       {"avatar": make_image("avatar.png",
                                                             fmt="PNG")},
                                       format="multipart")
        assert r.status_code == 200
        client_user.refresh_from_db()
        assert client_user.avatar

    def test_json_bilan_ham_ishlaydi(self, auth_as, client_user):
        r = auth_as(client_user).patch("/api/auth/profile/",
                                       {"full_name": "Yangi"}, format="json")
        assert r.status_code == 200


# =====================================================================
# Tasdiqlash endi hujjatga bog'liq
# =====================================================================
class TestTasdiqlashHujjatBilan:
    def test_hujjatsiz_tasdiqlab_bolmaydi(self, auth_as, admin_user):
        d = NoDocsDriverFactory()
        r = auth_as(admin_user).patch(f"/api/admin/drivers/{d.id}/approve/",
                                      {}, format="json")
        assert r.status_code == 400
        assert "yetishmayapti" in r.json()["message"].lower()
        d.refresh_from_db()
        assert not d.is_active

    def test_hujjat_bilan_tasdiqlanadi(self, auth_as, admin_user):
        d = UnapprovedDriverFactory()
        r = auth_as(admin_user).patch(f"/api/admin/drivers/{d.id}/approve/",
                                      {}, format="json")
        assert r.status_code == 200
        d.refresh_from_db()
        assert d.is_active

    def test_admin_api_hujjat_holatini_qaytaradi(self, auth_as, admin_user):
        NoDocsDriverFactory()
        d = data_of(auth_as(admin_user).get("/api/admin/drivers/"))
        rec = d["results"][0]
        assert rec["documents_complete"] is False
        assert rec["missing_documents"]

    def test_admin_panel_bulk_hujjatsizni_otkazadi(self, superuser=None):
        pass  # test_admin_site.py da


# =====================================================================
# Sharh va reyting
# =====================================================================
class TestSharh:
    def url(self, order):
        return f"/api/orders/{order.id}/review/"

    def test_mijoz_baho_beradi(self, auth_as, client_user, driver, tariff):
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        r = auth_as(client_user).post(self.url(o),
                                      {"rating": 4, "comment": "Yaxshi"},
                                      format="json")
        assert r.status_code == 201
        assert Review.objects.filter(order=o,
                                     kind=ReviewKind.CLIENT_TO_DRIVER).exists()

    def test_haydovchi_mijozni_baholaydi(self, auth_as, client_user, driver,
                                         tariff):
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        r = auth_as(driver.user).post(self.url(o), {"rating": 5},
                                      format="json")
        assert r.status_code == 201
        assert Review.objects.filter(order=o,
                                     kind=ReviewKind.DRIVER_TO_CLIENT).exists()

    def test_yakunlanmagan_safarga_baho_yoq(self, auth_as, client_user, driver,
                                            tariff):
        o = OrderFactory(client=client_user, driver=driver, tariff=tariff,
                         status=OrderStatus.ONGOING)
        r = auth_as(client_user).post(self.url(o), {"rating": 5},
                                      format="json")
        assert r.status_code == 400

    def test_begona_baho_bera_olmaydi(self, auth_as, other_client, driver,
                                      tariff):
        o = CompletedOrderFactory(driver=driver, tariff=tariff)
        r = auth_as(other_client).post(self.url(o), {"rating": 5},
                                       format="json")
        assert r.status_code == 403

    def test_ikki_marta_baho_berib_bolmaydi(self, auth_as, client_user, driver,
                                            tariff):
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        c = auth_as(client_user)
        assert c.post(self.url(o), {"rating": 5}, format="json").status_code == 201
        assert c.post(self.url(o), {"rating": 1}, format="json").status_code == 409

    @pytest.mark.parametrize("rating", [0, 6, -1, "besh"])
    def test_notogri_baho(self, auth_as, client_user, driver, tariff, rating):
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        r = auth_as(client_user).post(self.url(o), {"rating": rating},
                                      format="json")
        assert r.status_code == 400

    def test_sharhlarni_oqish(self, auth_as, client_user, driver, tariff):
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        ReviewFactory(order=o, author=client_user)
        r = auth_as(client_user).get(self.url(o))
        assert r.status_code == 200
        assert len(data_of(r)) == 1

    def test_mavjud_bolmagan_buyurtma(self, auth_as, client_user):
        r = auth_as(client_user).post("/api/orders/999999/review/",
                                      {"rating": 5}, format="json")
        assert r.status_code == 404


class TestReyting:
    def test_baho_reytingni_yangilaydi(self, auth_as, client_user, driver,
                                       tariff):
        assert float(driver.rating) == 5.0
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        auth_as(client_user).post(f"/api/orders/{o.id}/review/",
                                  {"rating": 3}, format="json")
        driver.refresh_from_db()
        assert float(driver.rating) == 3.0

    def test_ortacha_hisoblanadi(self, driver, tariff):
        for baho in (5, 4, 3):
            o = CompletedOrderFactory(driver=driver, tariff=tariff)
            ReviewFactory(order=o, author=o.client, rating=baho)
        recalculate_driver_rating(driver)
        driver.refresh_from_db()
        assert float(driver.rating) == 4.0

    def test_sharhsiz_haydovchi_5_qoladi(self, driver):
        recalculate_driver_rating(driver)
        driver.refresh_from_db()
        assert float(driver.rating) == 5.0

    def test_haydovchidan_mijozga_baho_reytingga_tasir_qilmaydi(
        self, auth_as, client_user, driver, tariff
    ):
        o = CompletedOrderFactory(client=client_user, driver=driver,
                                  tariff=tariff)
        auth_as(driver.user).post(f"/api/orders/{o.id}/review/",
                                  {"rating": 1}, format="json")
        driver.refresh_from_db()
        assert float(driver.rating) == 5.0


# =====================================================================
# available/ masofa filtri
# =====================================================================
class TestOchiqBuyurtmalarMasofasi:
    def test_uzoq_buyurtma_korinmaydi(self, auth_as, tariff):
        d = DriverFactory(location=point(41.3110, 69.2405))  # Toshkent
        # Samarqand — ~270 km
        OrderFactory(tariff=tariff, from_location=point(39.6270, 66.9750))
        r = auth_as(d.user).get("/api/orders/available/")
        assert len(data_of(r)) == 0

    def test_yaqin_buyurtma_korinadi(self, auth_as, tariff):
        d = DriverFactory(location=point(41.3110, 69.2405))
        OrderFactory(tariff=tariff, from_location=point(41.3200, 69.2500))
        r = auth_as(d.user).get("/api/orders/available/")
        assert len(data_of(r)) == 1

    def test_radius_parametri(self, auth_as, tariff):
        d = DriverFactory(location=point(41.3110, 69.2405))
        OrderFactory(tariff=tariff, from_location=point(41.5000, 69.5000))
        assert len(data_of(auth_as(d.user).get(
            "/api/orders/available/?radius=1000"))) == 0
        assert len(data_of(auth_as(d.user).get(
            "/api/orders/available/?radius=50000"))) == 1

    def test_notogri_radius_sukut_qiymatga_qaytadi(self, auth_as, tariff):
        d = DriverFactory(location=point(41.3110, 69.2405))
        OrderFactory(tariff=tariff, from_location=point(41.3200, 69.2500))
        r = auth_as(d.user).get("/api/orders/available/?radius=salom")
        assert r.status_code == 200
        assert len(data_of(r)) == 1

    def test_joylashuvsiz_haydovchi_hammasini_koradi(self, auth_as, tariff):
        d = DriverFactory(location=None)
        OrderFactory(tariff=tariff, from_location=point(39.6270, 66.9750))
        r = auth_as(d.user).get("/api/orders/available/")
        assert len(data_of(r)) == 1


# =====================================================================
# To'y narxi endi sozlanadi
# =====================================================================
class TestToyNarxi:
    def _post(self, api, hours=4, cars=3):
        return api.post("/api/wedding/requests/", {
            "car_brand": "Malibu", "car_count": cars, "address": "Chilonzor",
            "date": "2026-09-15", "duration_hours": hours,
            "contact_name": "Nodir", "contact_phone": "+998901234500",
        }, format="json")

    def test_sukut_narx(self, api):
        r = self._post(api)
        assert data_of(r)["estimated_price"] == 3 * 4 * 125_000

    def test_settingsdan_oqiladi(self, api, settings):
        settings.WEDDING_HOURLY_RATE = 200_000
        r = self._post(api, hours=2, cars=1)
        assert data_of(r)["estimated_price"] == 400_000
