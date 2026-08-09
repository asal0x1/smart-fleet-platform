"""Auth: register, login, OTP, logout, parol o'zgartirish/tiklash."""
import pytest

from apps.users.models import User
from apps.users.otp import OTPCode
from tests.conftest import data_of
from tests.factories import TEST_PASSWORD, ClientFactory

pytestmark = pytest.mark.django_db


class TestRegister:
    def test_muvaffaqiyatli(self, api):
        r = api.post("/api/auth/register/", {
            "phone": "+998901112233", "password": "Parol12345", "full_name": "Ali",
        }, format="json")
        assert r.status_code == 201
        assert User.objects.filter(phone="+998901112233").exists()
        assert data_of(r)["role"] == "client"

    def test_raqam_normalizatsiya_qilinadi(self, api):
        api.post("/api/auth/register/", {
            "phone": "90 111 22 33", "password": "Parol12345",
        }, format="json")
        assert User.objects.filter(phone="+998901112233").exists()

    def test_parol_hash_qilinadi(self, api):
        api.post("/api/auth/register/",
                 {"phone": "+998901112233", "password": "Parol12345"}, format="json")
        u = User.objects.get(phone="+998901112233")
        assert u.password != "Parol12345"
        assert u.check_password("Parol12345")

    def test_takroriy_raqam(self, api, client_user):
        r = api.post("/api/auth/register/",
                     {"phone": client_user.phone, "password": "Parol12345"},
                     format="json")
        assert r.status_code == 400

    @pytest.mark.parametrize("phone", ["12345", "+79991234567", "salom"])
    def test_notogri_raqam(self, api, phone):
        r = api.post("/api/auth/register/",
                     {"phone": phone, "password": "Parol12345"}, format="json")
        assert r.status_code == 400

    def test_qisqa_parol(self, api):
        r = api.post("/api/auth/register/",
                     {"phone": "+998901112233", "password": "123"}, format="json")
        assert r.status_code == 400

    def test_admin_roli_bilan_royxatdan_otib_bolmaydi(self, api):
        r = api.post("/api/auth/register/", {
            "phone": "+998901112233", "password": "Parol12345", "role": "admin",
        }, format="json")
        assert r.status_code == 400


class TestLogin:
    def test_muvaffaqiyatli(self, api, client_user):
        r = api.post("/api/auth/login/",
                     {"phone": client_user.phone, "password": TEST_PASSWORD},
                     format="json")
        assert r.status_code == 200
        d = data_of(r)
        assert d["access_token"] and d["refresh_token"]
        assert isinstance(d["expires_in"], int)

    def test_notogri_parol(self, api, client_user):
        r = api.post("/api/auth/login/",
                     {"phone": client_user.phone, "password": "yolgon"},
                     format="json")
        assert r.status_code == 400

    def test_mavjud_bolmagan_raqam(self, api):
        r = api.post("/api/auth/login/",
                     {"phone": "+998999999999", "password": "x"}, format="json")
        assert r.status_code == 400

    def test_bloklangan_hisob(self, api, client_user):
        client_user.is_active = False
        client_user.save()
        r = api.post("/api/auth/login/",
                     {"phone": client_user.phone, "password": TEST_PASSWORD},
                     format="json")
        assert r.status_code == 400


class TestOTP:
    def test_yuborish_va_tasdiqlash(self, api, client_user):
        r = api.post("/api/auth/send-otp/", {"phone": client_user.phone},
                     format="json")
        assert r.status_code == 200
        otp = OTPCode.objects.filter(phone=client_user.phone).first()
        assert otp is not None

        r = api.post("/api/auth/verify-otp/",
                     {"phone": client_user.phone, "otp": otp.code}, format="json")
        assert r.status_code == 200
        client_user.refresh_from_db()
        assert client_user.is_verified

    def test_notogri_kod(self, api, client_user):
        OTPCode.generate(client_user.phone)
        r = api.post("/api/auth/verify-otp/",
                     {"phone": client_user.phone, "otp": "000000"}, format="json")
        assert r.status_code == 400

    def test_muddati_otgan_kod(self, api, client_user):
        from django.utils import timezone
        otp = OTPCode.generate(client_user.phone)
        otp.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        otp.save()
        r = api.post("/api/auth/verify-otp/",
                     {"phone": client_user.phone, "otp": otp.code}, format="json")
        assert r.status_code == 400

    def test_kod_bir_marta_ishlatiladi(self, api, client_user):
        otp = OTPCode.generate(client_user.phone)
        body = {"phone": client_user.phone, "otp": otp.code}
        assert api.post("/api/auth/verify-otp/", body, format="json").status_code == 200
        assert api.post("/api/auth/verify-otp/", body, format="json").status_code == 400

    def test_yangi_kod_eskisini_bekor_qiladi(self, api, client_user):
        eski = OTPCode.generate(client_user.phone)
        OTPCode.generate(client_user.phone)
        r = api.post("/api/auth/verify-otp/",
                     {"phone": client_user.phone, "otp": eski.code}, format="json")
        assert r.status_code == 400


class TestLogout:
    def _login(self, api, user):
        r = api.post("/api/auth/login/",
                     {"phone": user.phone, "password": TEST_PASSWORD}, format="json")
        return data_of(r)

    def test_logout_refresh_tokenni_bekor_qiladi(self, api, auth_as, client_user):
        tokens = self._login(api, client_user)
        c = auth_as(client_user)
        r = c.post("/api/auth/logout/",
                   {"refresh_token": tokens["refresh_token"]}, format="json")
        assert r.status_code == 200

        r = api.post("/api/auth/refresh/",
                     {"refresh": tokens["refresh_token"]}, format="json")
        assert r.status_code == 401

    def test_rotatsiyadan_keyin_eski_refresh_ishlamaydi(self, api, client_user):
        tokens = self._login(api, client_user)
        r = api.post("/api/auth/refresh/",
                     {"refresh": tokens["refresh_token"]}, format="json")
        assert r.status_code == 200
        r2 = api.post("/api/auth/refresh/",
                      {"refresh": tokens["refresh_token"]}, format="json")
        assert r2.status_code == 401

    def test_token_yoq(self, api):
        r = api.post("/api/auth/logout/", {"refresh_token": "x"}, format="json")
        assert r.status_code == 401

    def test_notogri_token(self, auth_as, client_user):
        c = auth_as(client_user)
        r = c.post("/api/auth/logout/", {"refresh_token": "yolgon"}, format="json")
        assert r.status_code == 400


class TestChangePassword:
    def test_muvaffaqiyatli(self, auth_as, client_user):
        c = auth_as(client_user)
        r = c.post("/api/auth/change-password/", {
            "old_password": TEST_PASSWORD, "new_password": "YangiParol99",
        }, format="json")
        assert r.status_code == 200
        client_user.refresh_from_db()
        assert client_user.check_password("YangiParol99")

    def test_notogri_joriy_parol(self, auth_as, client_user):
        c = auth_as(client_user)
        r = c.post("/api/auth/change-password/", {
            "old_password": "yolgon", "new_password": "YangiParol99",
        }, format="json")
        assert r.status_code == 400

    def test_bir_xil_parol_rad_etiladi(self, auth_as, client_user):
        c = auth_as(client_user)
        r = c.post("/api/auth/change-password/", {
            "old_password": TEST_PASSWORD, "new_password": TEST_PASSWORD,
        }, format="json")
        assert r.status_code == 400

    def test_zaif_parol_rad_etiladi(self, auth_as, client_user):
        c = auth_as(client_user)
        r = c.post("/api/auth/change-password/", {
            "old_password": TEST_PASSWORD, "new_password": "123",
        }, format="json")
        assert r.status_code == 400

    def test_token_yoq(self, api):
        r = api.post("/api/auth/change-password/", {}, format="json")
        assert r.status_code == 401


class TestResetPassword:
    def test_otp_bilan_tiklash(self, api, client_user):
        otp = OTPCode.generate(client_user.phone)
        r = api.post("/api/auth/reset-password/", {
            "phone": client_user.phone, "otp": otp.code,
            "new_password": "TiklanganP1",
        }, format="json")
        assert r.status_code == 200
        client_user.refresh_from_db()
        assert client_user.check_password("TiklanganP1")

    def test_notogri_otp(self, api, client_user):
        OTPCode.generate(client_user.phone)
        r = api.post("/api/auth/reset-password/", {
            "phone": client_user.phone, "otp": "000000",
            "new_password": "TiklanganP1",
        }, format="json")
        assert r.status_code == 400

    def test_mavjud_bolmagan_raqam_uchun_xabar_farq_qilmaydi(self, api):
        """User bor-yo'qligini aniqlab olishga yo'l qo'ymaslik kerak."""
        otp = OTPCode.generate("+998995554433")
        r = api.post("/api/auth/reset-password/", {
            "phone": "+998995554433", "otp": otp.code,
            "new_password": "TiklanganP1",
        }, format="json")
        assert r.status_code == 400

    def test_bloklangan_hisob(self, api, client_user):
        client_user.is_active = False
        client_user.save()
        otp = OTPCode.generate(client_user.phone)
        r = api.post("/api/auth/reset-password/", {
            "phone": client_user.phone, "otp": otp.code,
            "new_password": "TiklanganP1",
        }, format="json")
        assert r.status_code == 403


class TestProfile:
    def test_oqish(self, auth_as, client_user):
        r = auth_as(client_user).get("/api/auth/profile/")
        assert r.status_code == 200
        assert data_of(r)["phone"] == client_user.phone

    def test_tahrirlash(self, auth_as, client_user):
        r = auth_as(client_user).patch("/api/auth/profile/",
                                       {"full_name": "Yangi Ism"}, format="json")
        assert r.status_code == 200
        client_user.refresh_from_db()
        assert client_user.full_name == "Yangi Ism"

    def test_rolni_ozgartirib_bolmaydi(self, auth_as, client_user):
        auth_as(client_user).patch("/api/auth/profile/",
                                   {"role": "admin"}, format="json")
        client_user.refresh_from_db()
        assert client_user.role == "client"

    def test_token_yoq(self, api):
        assert api.get("/api/auth/profile/").status_code == 401
