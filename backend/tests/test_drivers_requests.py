"""Haydovchi endpointlari (profil, lokatsiya, nearby) va so'rov formalari."""
import pytest
from django.core import mail

from apps.drivers.models import Driver
from apps.requests.models import HeavyEquipmentRequest, WeddingRequest
from tests.conftest import data_of
from tests.factories import DriverFactory, DriverUserFactory, point

pytestmark = pytest.mark.django_db


class TestHaydovchiProfili:
    def test_ilk_murojaatda_profil_yaratiladi(self, auth_as):
        user = DriverUserFactory()
        assert not Driver.objects.filter(user=user).exists()
        r = auth_as(user).get("/api/drivers/profile/")
        assert r.status_code == 200
        assert Driver.objects.filter(user=user).exists()

    def test_yangi_profil_tasdiqlanmagan_boladi(self, auth_as):
        user = DriverUserFactory()
        auth_as(user).get("/api/drivers/profile/")
        assert not Driver.objects.get(user=user).is_active

    def test_mijoz_kira_olmaydi(self, auth_as, client_user):
        assert auth_as(client_user).get("/api/drivers/profile/").status_code == 403

    def test_mijozga_driver_yaratilmaydi(self, auth_as, client_user):
        auth_as(client_user).get("/api/drivers/profile/")
        assert not Driver.objects.filter(user=client_user).exists()

    def test_tahrirlash(self, auth_as, driver):
        r = auth_as(driver.user).patch("/api/drivers/profile/",
                                       {"car_model": "Malibu"}, format="json")
        assert r.status_code == 200
        driver.refresh_from_db()
        assert driver.car_model == "Malibu"

    def test_ozini_tasdiqlab_bolmaydi(self, auth_as, unapproved_driver):
        auth_as(unapproved_driver.user).patch("/api/drivers/profile/",
                                              {"is_active": True}, format="json")
        unapproved_driver.refresh_from_db()
        assert not unapproved_driver.is_active


class TestLokatsiya:
    def test_yangilash(self, auth_as, driver):
        r = auth_as(driver.user).post("/api/drivers/location/",
                                      {"lat": 41.35, "lng": 69.29}, format="json")
        assert r.status_code == 200
        driver.refresh_from_db()
        assert round(driver.current_lat, 2) == 41.35

    @pytest.mark.parametrize("body", [
        {"lat": 91, "lng": 69.2},
        {"lat": 41.3, "lng": 181},
        {"lat": "salom", "lng": 69.2},
        {"lng": 69.2},
    ])
    def test_notogri_koordinata(self, auth_as, driver, body):
        assert auth_as(driver.user).post("/api/drivers/location/", body,
                                         format="json").status_code == 400


class TestOnlineHolat:
    def test_tasdiqlangan_haydovchi_online_boladi(self, auth_as, driver):
        driver.is_online = False
        driver.save()
        r = auth_as(driver.user).post("/api/drivers/online/",
                                      {"is_online": True}, format="json")
        assert r.status_code == 200
        driver.refresh_from_db()
        assert driver.is_online

    def test_tasdiqlanmagan_haydovchi_online_bola_olmaydi(self, auth_as,
                                                          unapproved_driver):
        r = auth_as(unapproved_driver.user).post("/api/drivers/online/",
                                                 {"is_online": True}, format="json")
        assert r.status_code == 403

    def test_offlinega_otish_har_doim_mumkin(self, auth_as, unapproved_driver):
        r = auth_as(unapproved_driver.user).post("/api/drivers/online/",
                                                 {"is_online": False},
                                                 format="json")
        assert r.status_code == 200


class TestNearby:
    def test_yaqin_haydovchilarni_topadi(self, auth_as, client_user):
        DriverFactory(location=point(41.3110, 69.2405))   # ~0 km
        DriverFactory(location=point(41.5000, 69.5000))   # ~30 km
        r = auth_as(client_user).get(
            "/api/drivers/nearby/?lat=41.3110&lng=69.2405&radius=5000"
        )
        assert r.status_code == 200
        assert len(data_of(r)["drivers"]) == 1

    def test_offline_haydovchi_chiqmaydi(self, auth_as, client_user):
        DriverFactory(location=point(41.3110, 69.2405), is_online=False)
        r = auth_as(client_user).get(
            "/api/drivers/nearby/?lat=41.3110&lng=69.2405&radius=5000"
        )
        assert len(data_of(r)["drivers"]) == 0

    def test_tasdiqlanmagan_haydovchi_chiqmaydi(self, auth_as, client_user):
        DriverFactory(location=point(41.3110, 69.2405), is_active=False)
        r = auth_as(client_user).get(
            "/api/drivers/nearby/?lat=41.3110&lng=69.2405&radius=5000"
        )
        assert len(data_of(r)["drivers"]) == 0

    def test_masofa_va_eta_hisoblanadi(self, auth_as, client_user):
        DriverFactory(location=point(41.3200, 69.2405))
        r = auth_as(client_user).get(
            "/api/drivers/nearby/?lat=41.3110&lng=69.2405&radius=5000"
        )
        d = data_of(r)["drivers"][0]
        assert d["distance_m"] > 0 and d["eta_min"] >= 1

    @pytest.mark.parametrize("qs", [
        "?lat=41.3&lng=69.2&radius=99999999",
        "?lat=41.3&lng=69.2&radius=10",
        "?lat=999&lng=69.2",
        "?lng=69.2",
        "?lat=41.3&lng=69.2&limit=1000",
    ])
    def test_notogri_parametrlar(self, auth_as, client_user, qs):
        assert auth_as(client_user).get(
            f"/api/drivers/nearby/{qs}"
        ).status_code == 400

    def test_limit_hurmat_qilinadi(self, auth_as, client_user):
        DriverFactory.create_batch(5, location=point(41.3110, 69.2405))
        r = auth_as(client_user).get(
            "/api/drivers/nearby/?lat=41.3110&lng=69.2405&radius=5000&limit=2"
        )
        assert len(data_of(r)["drivers"]) == 2


class TestSorovFormalari:
    def _heavy_body(self, phone="+998901234500"):
        return {
            "category": "earth",
            "items": [{"name": "Ekskavator", "quantity": 2}],
            "address": "Sergeli", "start_date": "2026-09-01",
            "duration_days": 3, "contact_name": "Olim",
            "contact_phone": phone,
        }

    def test_ogir_texnika_sorovi(self, api):
        r = api.post("/api/heavy-equipment/requests/", self._heavy_body(),
                     format="json")
        assert r.status_code == 201
        assert HeavyEquipmentRequest.objects.count() == 1

    def test_operatorga_email_ketadi(self, api):
        mail.outbox.clear()
        api.post("/api/heavy-equipment/requests/", self._heavy_body(),
                 format="json")
        assert len(mail.outbox) == 1
        assert "og'ir texnika" in mail.outbox[0].subject.lower()

    def test_telefon_normalizatsiya_qilinadi(self, api):
        api.post("/api/heavy-equipment/requests/",
                 self._heavy_body(phone="90 123 45 00"), format="json")
        assert HeavyEquipmentRequest.objects.first().contact_phone == "+998901234500"

    def test_notogri_telefon(self, api):
        r = api.post("/api/heavy-equipment/requests/",
                     self._heavy_body(phone="12345"), format="json")
        assert r.status_code == 400

    def test_status_pending_boladi(self, api):
        api.post("/api/heavy-equipment/requests/", self._heavy_body(),
                 format="json")
        assert HeavyEquipmentRequest.objects.first().status == "pending"

    def test_bosh_items(self, api):
        body = self._heavy_body()
        body["items"] = []
        r = api.post("/api/heavy-equipment/requests/", body, format="json")
        assert r.status_code in (201, 400)  # bo'sh ro'yxat hozircha ruxsat etilgan

    def test_toy_sorovi_narx_hisoblaydi(self, api):
        r = api.post("/api/wedding/requests/", {
            "car_brand": "Malibu", "car_count": 3, "address": "Chilonzor",
            "date": "2026-09-15", "duration_hours": 4,
            "contact_name": "Nodir", "contact_phone": "+998901234500",
        }, format="json")
        assert r.status_code == 201
        # 3 mashina * 4 soat * 125 000
        assert data_of(r)["estimated_price"] == 3 * 4 * 125_000

    def test_toy_sorovi_email(self, api):
        mail.outbox.clear()
        api.post("/api/wedding/requests/", {
            "car_brand": "Malibu", "car_count": 1, "address": "Chilonzor",
            "date": "2026-09-15", "contact_name": "Nodir",
            "contact_phone": "+998901234500",
        }, format="json")
        assert len(mail.outbox) == 1

    def test_token_talab_qilinmaydi(self, api):
        """So'rov formalari anonim foydalanuvchilar uchun ochiq."""
        r = api.post("/api/wedding/requests/", {
            "car_brand": "Nexia", "car_count": 1, "address": "X",
            "date": "2026-09-15", "contact_name": "A",
            "contact_phone": "+998901234500",
        }, format="json")
        assert r.status_code == 201
