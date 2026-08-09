"""Rate limiting testlari.

Cheklovlar `.env` orqali sozlanadi, shuning uchun testlar `throttle_rate`
fixture'i bilan aniq qiymat o'rnatadi — standart qiymat o'zgarsa
testlar sinmasin.
"""
import pytest

from apps.users.otp import OTPCode
from tests.factories import TEST_PASSWORD

pytestmark = pytest.mark.django_db


class TestOTPThrottle:
    def test_uchinchidan_keyin_bloklanadi(self, api, throttle_rate):
        throttle_rate("otp", "3/hour")
        phone = "+998901112233"
        codes = [
            api.post("/api/auth/send-otp/", {"phone": phone},
                     format="json").status_code
            for _ in range(4)
        ]
        assert codes == [200, 200, 200, 429]

    def test_cheklov_raqam_boyicha_ishlaydi(self, api, throttle_rate):
        """IP emas, telefon bo'yicha — boshqa raqamga SMS ketaverishi kerak."""
        throttle_rate("otp", "2/hour")
        for _ in range(2):
            api.post("/api/auth/send-otp/", {"phone": "+998901112233"},
                     format="json")
        assert api.post("/api/auth/send-otp/", {"phone": "+998901112233"},
                        format="json").status_code == 429
        assert api.post("/api/auth/send-otp/", {"phone": "+998904445566"},
                        format="json").status_code == 200

    def test_turli_formatdagi_bir_xil_raqam_bir_hisoblanadi(self, api, throttle_rate):
        """Normalizatsiya bo'lmasa hujumchi '998..' va '+998..' bilan aylanib o'tardi."""
        throttle_rate("otp", "2/hour")
        api.post("/api/auth/send-otp/", {"phone": "+998901112233"}, format="json")
        api.post("/api/auth/send-otp/", {"phone": "998901112233"}, format="json")
        r = api.post("/api/auth/send-otp/", {"phone": "90 111 22 33"}, format="json")
        assert r.status_code == 429


class TestOTPVerifyThrottle:
    def test_brute_force_bloklanadi(self, api, throttle_rate, client_user):
        throttle_rate("otp_verify", "5/hour")
        OTPCode.generate(client_user.phone)
        codes = [
            api.post("/api/auth/verify-otp/",
                     {"phone": client_user.phone, "otp": "000000"},
                     format="json").status_code
            for _ in range(6)
        ]
        assert codes[-1] == 429


class TestLoginThrottle:
    def test_parol_terishga_urinish_bloklanadi(self, api, throttle_rate, client_user):
        throttle_rate("login", "5/hour")
        codes = [
            api.post("/api/auth/login/",
                     {"phone": client_user.phone, "password": "yolgon"},
                     format="json").status_code
            for _ in range(6)
        ]
        assert codes[-1] == 429

    def test_muvaffaqiyatli_loginlar_ham_hisoblanadi(self, api, throttle_rate, client_user):
        throttle_rate("login", "2/hour")
        body = {"phone": client_user.phone, "password": TEST_PASSWORD}
        assert api.post("/api/auth/login/", body, format="json").status_code == 200
        assert api.post("/api/auth/login/", body, format="json").status_code == 200
        assert api.post("/api/auth/login/", body, format="json").status_code == 429


class TestRegisterThrottle:
    def test_bloklanadi(self, api, throttle_rate):
        throttle_rate("register", "3/hour")
        codes = []
        for i in range(4):
            codes.append(api.post("/api/auth/register/", {
                "phone": f"+99890111{i:04d}", "password": "Parol12345",
            }, format="json").status_code)
        assert codes[-1] == 429


class TestSorovFormasiThrottle:
    def _heavy(self, api):
        return api.post("/api/heavy-equipment/requests/", {
            "category": "earth",
            "items": [{"name": "Ekskavator", "quantity": 1}],
            "address": "Toshkent", "start_date": "2026-09-01",
            "contact_name": "Test", "contact_phone": "+998901234500",
        }, format="json")

    def test_spam_bloklanadi(self, api, throttle_rate):
        throttle_rate("request_form", "3/hour")
        codes = [self._heavy(api).status_code for _ in range(4)]
        assert codes[:3] == [201, 201, 201]
        assert codes[-1] == 429

    def test_toy_sorovi_ham_bir_hisoblagichda(self, api, throttle_rate):
        throttle_rate("request_form", "2/hour")
        self._heavy(api)
        self._heavy(api)
        r = api.post("/api/wedding/requests/", {
            "car_brand": "Malibu", "car_count": 2, "address": "Toshkent",
            "date": "2026-09-15", "contact_name": "Test",
            "contact_phone": "+998901234500",
        }, format="json")
        assert r.status_code == 429


class TestParolTiklashThrottle:
    def test_bloklanadi(self, api, throttle_rate, client_user):
        throttle_rate("password_reset", "2/hour")
        body = {"phone": client_user.phone, "otp": "000000",
                "new_password": "YangiParol9"}
        api.post("/api/auth/reset-password/", body, format="json")
        api.post("/api/auth/reset-password/", body, format="json")
        assert api.post("/api/auth/reset-password/", body,
                        format="json").status_code == 429
