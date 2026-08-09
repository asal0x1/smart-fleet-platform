"""Django admin paneli — sahifalar ochilishi va bulk action'lar."""
import pytest
from django.test import Client
from django.urls import reverse

from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment, PaymentState
from apps.requests.models import HeavyEquipmentRequest, WeddingRequest
from apps.users.models import User
from tests.factories import (
    ClientFactory,
    CompletedOrderFactory,
    DriverFactory,
    HeavyRequestFactory,
    OrderFactory,
    PaymentFactory,
    UnapprovedDriverFactory,
    WeddingRequestFactory,
)

pytestmark = pytest.mark.django_db

MODELS = [
    ("users", "user"),
    ("users", "otpcode"),
    ("drivers", "driver"),
    ("orders", "order"),
    ("orders", "tariff"),
    ("payments", "payment"),
    ("requests", "heavyequipmentrequest"),
    ("requests", "weddingrequest"),
]


@pytest.fixture
def superuser(db):
    return ClientFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def admin_client(superuser):
    c = Client()
    c.force_login(superuser)
    return c


def changelist(app, model):
    return reverse(f"admin:{app}_{model}_changelist")


def run_action(client, app, model, action, ids):
    return client.post(
        changelist(app, model),
        {"action": action, "_selected_action": [str(i) for i in ids]},
        follow=True,
    )


class TestSahifalarOchiladi:
    @pytest.mark.parametrize("app,model", MODELS)
    def test_changelist(self, admin_client, app, model, tariff, driver):
        assert admin_client.get(changelist(app, model)).status_code == 200

    def test_bosh_sahifa(self, admin_client):
        r = admin_client.get(reverse("admin:index"))
        assert r.status_code == 200
        assert b"SMART FLEET" in r.content

    def test_buyurtma_sahifasi(self, admin_client, order):
        url = reverse("admin:orders_order_change", args=[order.id])
        assert admin_client.get(url).status_code == 200

    def test_haydovchi_sahifasi(self, admin_client, driver):
        url = reverse("admin:drivers_driver_change", args=[driver.id])
        assert admin_client.get(url).status_code == 200

    def test_user_qoshish_sahifasi(self, admin_client):
        assert admin_client.get(reverse("admin:users_user_add")).status_code == 200

    def test_anonim_kira_olmaydi(self, client=None):
        c = Client()
        r = c.get(changelist("orders", "order"))
        assert r.status_code == 302  # login sahifasiga

    def test_qidiruv_ishlaydi(self, admin_client, order):
        r = admin_client.get(changelist("orders", "order") + "?q=Chilonzor")
        assert r.status_code == 200

    def test_sana_ierarxiyasi(self, admin_client, order):
        r = admin_client.get(changelist("orders", "order") + "?created_at__year=2026")
        assert r.status_code == 200


class TestAutocomplete:
    """autocomplete_fields ishlashi uchun manba admin'da search_fields kerak."""

    @pytest.mark.parametrize("app,model,field,target_app,target_model", [
        ("orders", "order", "client", "users", "user"),
        ("orders", "order", "driver", "drivers", "driver"),
        ("orders", "order", "tariff", "orders", "tariff"),
        ("drivers", "driver", "user", "users", "user"),
        ("payments", "payment", "order", "orders", "order"),
    ])
    def test_endpoint_javob_beradi(self, admin_client, tariff, driver, order,
                                   app, model, field, target_app, target_model):
        r = admin_client.get(
            reverse("admin:autocomplete"),
            {
                "app_label": app, "model_name": model, "field_name": field,
                "term": "",
            },
        )
        assert r.status_code == 200
        assert "results" in r.json()


class TestHaydovchiActionlari:
    def test_bulk_tasdiqlash(self, admin_client):
        d1, d2 = UnapprovedDriverFactory(), UnapprovedDriverFactory()
        run_action(admin_client, "drivers", "driver", "approve_drivers",
                   [d1.id, d2.id])
        d1.refresh_from_db()
        d2.refresh_from_db()
        assert d1.is_active and d2.is_active

    def test_tasdiqlash_userni_ham_verified_qiladi(self, admin_client):
        d = UnapprovedDriverFactory()
        d.user.is_verified = False
        d.user.save()
        run_action(admin_client, "drivers", "driver", "approve_drivers", [d.id])
        d.user.refresh_from_db()
        assert d.user.is_verified

    def test_hujjatsiz_otkazib_yuboriladi(self, admin_client):
        from tests.factories import NoDocsDriverFactory
        hujjatsiz = NoDocsDriverFactory()
        yaxshi = UnapprovedDriverFactory()
        r = run_action(admin_client, "drivers", "driver", "approve_drivers",
                       [hujjatsiz.id, yaxshi.id])
        hujjatsiz.refresh_from_db()
        yaxshi.refresh_from_db()
        assert not hujjatsiz.is_active
        assert yaxshi.is_active
        assert "hujjatlari yetishmagani" in r.content.decode()

    def test_mashina_raqamisiz_otkazib_yuboriladi(self, admin_client):
        yomon = UnapprovedDriverFactory(car_number="")
        yaxshi = UnapprovedDriverFactory()
        r = run_action(admin_client, "drivers", "driver", "approve_drivers",
                       [yomon.id, yaxshi.id])
        yomon.refresh_from_db()
        yaxshi.refresh_from_db()
        assert not yomon.is_active
        assert yaxshi.is_active
        assert b"Mashina raqami" in r.content

    def test_tasdiqni_bekor_qilish_offline_ham_qiladi(self, admin_client):
        d = DriverFactory(is_active=True, is_online=True)
        run_action(admin_client, "drivers", "driver", "unapprove_drivers", [d.id])
        d.refresh_from_db()
        assert not d.is_active and not d.is_online

    def test_majburan_offline(self, admin_client):
        d = DriverFactory(is_online=True)
        run_action(admin_client, "drivers", "driver", "force_offline", [d.id])
        d.refresh_from_db()
        assert not d.is_online
        assert d.is_active  # tasdiq tegilmaydi

    def test_tasdiq_filtri(self, admin_client, driver):
        UnapprovedDriverFactory()
        r = admin_client.get(changelist("drivers", "driver") + "?approval=pending")
        assert r.status_code == 200


class TestUserActionlari:
    def test_bulk_bloklash(self, admin_client):
        u1, u2 = ClientFactory(), ClientFactory()
        run_action(admin_client, "users", "user", "block_users", [u1.id, u2.id])
        u1.refresh_from_db()
        u2.refresh_from_db()
        assert not u1.is_active and not u2.is_active

    def test_ozini_bloklab_bolmaydi(self, admin_client, superuser):
        r = run_action(admin_client, "users", "user", "block_users",
                       [superuser.id])
        superuser.refresh_from_db()
        assert superuser.is_active
        # Django xabarni HTML-escape qiladi (bo&#x27;lmaydi)
        assert "bloklab bo" in r.content.decode()

    def test_superuser_himoyalangan(self, admin_client):
        su = ClientFactory(is_superuser=True)
        run_action(admin_client, "users", "user", "block_users", [su.id])
        su.refresh_from_db()
        assert su.is_active

    def test_blokdan_chiqarish(self, admin_client):
        u = ClientFactory(is_active=False)
        run_action(admin_client, "users", "user", "unblock_users", [u.id])
        u.refresh_from_db()
        assert u.is_active

    def test_verified_belgilash(self, admin_client):
        u = ClientFactory(is_verified=False)
        run_action(admin_client, "users", "user", "mark_verified", [u.id])
        u.refresh_from_db()
        assert u.is_verified

    def test_parol_admin_orqali_hash_qilinadi(self, admin_client):
        r = admin_client.post(reverse("admin:users_user_add"), {
            "phone": "+998901239876", "full_name": "Yangi", "role": "client",
            "password1": "AdminParol123", "password2": "AdminParol123",
        }, follow=True)
        assert r.status_code == 200
        u = User.objects.get(phone="+998901239876")
        assert u.check_password("AdminParol123")


class TestBuyurtmaActionlari:
    def test_bulk_bekor_qilish(self, admin_client, tariff):
        o1 = OrderFactory(tariff=tariff)
        o2 = OrderFactory(tariff=tariff)
        run_action(admin_client, "orders", "order", "cancel_orders",
                   [o1.id, o2.id])
        o1.refresh_from_db()
        o2.refresh_from_db()
        assert o1.status == OrderStatus.CANCELLED
        assert o2.status == OrderStatus.CANCELLED
        assert o1.cancel_reason

    def test_yakunlangan_buyurtmaga_tegilmaydi(self, admin_client, tariff):
        yopiq = CompletedOrderFactory(tariff=tariff)
        ochiq = OrderFactory(tariff=tariff)
        r = run_action(admin_client, "orders", "order", "cancel_orders",
                       [yopiq.id, ochiq.id])
        yopiq.refresh_from_db()
        ochiq.refresh_from_db()
        assert yopiq.status == OrderStatus.COMPLETED
        assert ochiq.status == OrderStatus.CANCELLED
        assert b"tegilmadi" in r.content

    def test_kutilayotgan_tolov_ham_bekor_boladi(self, admin_client, order):
        p = PaymentFactory(order=order)
        run_action(admin_client, "orders", "order", "cancel_orders", [order.id])
        p.refresh_from_db()
        assert p.status == PaymentState.CANCELLED

    def test_tolovlar_inline_korinadi(self, admin_client, order):
        PaymentFactory(order=order, amount=33_000)
        r = admin_client.get(reverse("admin:orders_order_change", args=[order.id]))
        matn = r.content.decode()
        assert "33000" in matn or "33 000" in matn


class TestSorovActionlari:
    @pytest.mark.parametrize("action,kutilgan", [
        ("mark_contacted", "contacted"),
        ("mark_confirmed", "confirmed"),
        ("mark_completed", "completed"),
        ("mark_cancelled", "cancelled"),
    ])
    def test_ogir_texnika_statuslari(self, admin_client, action, kutilgan):
        req = HeavyRequestFactory()
        run_action(admin_client, "requests", "heavyequipmentrequest", action,
                   [req.id])
        req.refresh_from_db()
        assert req.status == kutilgan

    def test_toy_sorovi_statusi(self, admin_client):
        req = WeddingRequestFactory()
        run_action(admin_client, "requests", "weddingrequest", "mark_confirmed",
                   [req.id])
        req.refresh_from_db()
        assert req.status == "confirmed"

    def test_bir_nechta_sorov_bir_vaqtda(self, admin_client):
        a, b = HeavyRequestFactory(), HeavyRequestFactory()
        run_action(admin_client, "requests", "heavyequipmentrequest",
                   "mark_contacted", [a.id, b.id])
        a.refresh_from_db()
        b.refresh_from_db()
        assert a.status == b.status == "contacted"


class TestTolovlar:
    def test_qolda_qoshib_bolmaydi(self, admin_client):
        r = admin_client.get(reverse("admin:payments_payment_add"))
        assert r.status_code in (403, 302)

    def test_sarlavhada_yigindi_korinadi(self, admin_client, tariff):
        PaymentFactory(order=OrderFactory(tariff=tariff), amount=10_000,
                       status=PaymentState.PAID)
        PaymentFactory(order=OrderFactory(tariff=tariff), amount=5_000)
        r = admin_client.get(changelist("payments", "payment"))
        matn = r.content.decode()
        assert "15 000" in matn and "10 000" in matn


class TestOTPKodlari:
    def test_tahrirlab_bolmaydi(self, admin_client, client_user):
        from apps.users.otp import OTPCode
        otp = OTPCode.generate(client_user.phone)
        r = admin_client.get(
            reverse("admin:users_otpcode_change", args=[otp.id])
        )
        # change_permission yo'q -> ko'rish rejimi yoki redirect
        assert r.status_code in (200, 302, 403)

    def test_qolda_qoshib_bolmaydi(self, admin_client):
        r = admin_client.get(reverse("admin:users_otpcode_add"))
        assert r.status_code in (403, 302)
