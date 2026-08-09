"""Click to'lov integratsiyasi — imzo, summa, prepare_id, idempotentlik.

1-navbatda tuzatilgan ikkita jiddiy teshik shu yerda qamrab olinadi:
  - summa tekshirilmasligi (arzon narxda "to'lash")
  - merchant_prepare_id tekshirilmasligi (prepare'siz to'lov)
"""
import pytest

from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment, PaymentState
from services.payment import click_service
from tests.conftest import data_of
from tests.factories import OrderFactory, PaymentFactory

pytestmark = pytest.mark.django_db

PREPARE_URL = "/api/payments/click/prepare/"
COMPLETE_URL = "/api/payments/click/complete/"

# Click javob kodlari
OK = 0
SIGN_ERROR = -1
INVALID_AMOUNT = -2
ALREADY_PAID = -4
ORDER_NOT_FOUND = -5
TRANSACTION_NOT_FOUND = -6
CANCELLED = -9


@pytest.fixture
def paid_order(client_user, tariff):
    return OrderFactory(client=client_user, tariff=tariff, estimated_price=250_000)


@pytest.fixture
def pending_payment(paid_order):
    return PaymentFactory(order=paid_order, amount=250_000, method="click")


# =====================================================================
# Servis darajasidagi unit testlar
# =====================================================================
class TestCheckAmount:
    @pytest.mark.parametrize("received", ["250000", "250000.00", 250000, 250000.005])
    def test_togri_summalar(self, received):
        assert click_service.check_amount(received, 250_000)

    @pytest.mark.parametrize("received", ["1000", "249999", 0, -250000, "abc", None])
    def test_notogri_summalar(self, received):
        assert not click_service.check_amount(received, 250_000)


class TestIPWhitelist:
    def test_bosh_royxat_hammaga_ruxsat(self, settings):
        settings.CLICK_ALLOWED_IPS = []
        assert click_service.is_allowed_ip("1.2.3.4")

    def test_aniq_ip(self, settings):
        settings.CLICK_ALLOWED_IPS = ["213.230.106.10"]
        assert click_service.is_allowed_ip("213.230.106.10")
        assert not click_service.is_allowed_ip("8.8.8.8")

    def test_cidr(self, settings):
        settings.CLICK_ALLOWED_IPS = ["213.230.106.0/24"]
        assert click_service.is_allowed_ip("213.230.106.55")
        assert not click_service.is_allowed_ip("213.230.107.1")

    def test_notogri_ip(self, settings):
        settings.CLICK_ALLOWED_IPS = ["213.230.106.0/24"]
        assert not click_service.is_allowed_ip("salom")
        assert not click_service.is_allowed_ip(None)


# =====================================================================
# To'lov boshlash
# =====================================================================
class TestCreatePayment:
    def test_click_havolasi_qaytadi(self, auth_as, client_user, paid_order):
        r = auth_as(client_user).post("/api/payments/create/",
                                      {"order_id": paid_order.id, "method": "click"},
                                      format="json")
        assert r.status_code == 200
        d = data_of(r)
        assert "my.click.uz" in d["click_url"]
        assert d["amount"] == 250_000

    def test_begona_buyurtma(self, auth_as, other_client, paid_order):
        r = auth_as(other_client).post("/api/payments/create/",
                                       {"order_id": paid_order.id}, format="json")
        assert r.status_code == 404

    def test_bekor_qilingan_buyurtma(self, auth_as, client_user, paid_order):
        paid_order.status = OrderStatus.CANCELLED
        paid_order.save()
        r = auth_as(client_user).post("/api/payments/create/",
                                      {"order_id": paid_order.id}, format="json")
        assert r.status_code == 400

    def test_allaqachon_tolangan(self, auth_as, client_user, paid_order):
        paid_order.payment_status = "paid"
        paid_order.save()
        r = auth_as(client_user).post("/api/payments/create/",
                                      {"order_id": paid_order.id}, format="json")
        assert r.status_code == 400

    def test_qayta_bosilganda_yangi_payment_yaratilmaydi(
        self, auth_as, client_user, paid_order
    ):
        c = auth_as(client_user)
        body = {"order_id": paid_order.id, "method": "click"}
        c.post("/api/payments/create/", body, format="json")
        c.post("/api/payments/create/", body, format="json")
        assert Payment.objects.filter(order=paid_order).count() == 1

    def test_notogri_usul(self, auth_as, client_user, paid_order):
        r = auth_as(client_user).post("/api/payments/create/",
                                      {"order_id": paid_order.id, "method": "bitcoin"},
                                      format="json")
        assert r.status_code == 400


# =====================================================================
# Prepare
# =====================================================================
class TestClickPrepare:
    def test_muvaffaqiyatli(self, api, paid_order, pending_payment,
                            click_prepare_body):
        body = click_prepare_body(paid_order.id, 250000)
        r = api.post(PREPARE_URL, body, format="json")
        assert r.json()["error"] == OK
        assert r.json()["merchant_prepare_id"] == pending_payment.id

    def test_soxta_imzo(self, api, paid_order, pending_payment, click_prepare_body):
        body = click_prepare_body(paid_order.id, 250000)
        body["sign_string"] = "yolgon"
        assert api.post(PREPARE_URL, body, format="json").json()["error"] == SIGN_ERROR

    def test_arzon_summa_rad_etiladi(self, api, paid_order, pending_payment,
                                     click_prepare_body):
        """⚠️ Ilgari bu o'tib ketardi — 1000 so'mga 250 000 lik buyurtma."""
        body = click_prepare_body(paid_order.id, 1000)
        assert api.post(PREPARE_URL, body,
                        format="json").json()["error"] == INVALID_AMOUNT

    def test_mavjud_bolmagan_buyurtma(self, api, click_prepare_body):
        body = click_prepare_body(999999, 250000)
        assert api.post(PREPARE_URL, body,
                        format="json").json()["error"] == ORDER_NOT_FOUND

    def test_tolov_yaratilmagan(self, api, paid_order, click_prepare_body):
        body = click_prepare_body(paid_order.id, 250000)
        assert api.post(PREPARE_URL, body,
                        format="json").json()["error"] == TRANSACTION_NOT_FOUND

    def test_bekor_qilingan_buyurtma(self, api, paid_order, pending_payment,
                                     click_prepare_body):
        paid_order.status = OrderStatus.CANCELLED
        paid_order.save()
        body = click_prepare_body(paid_order.id, 250000)
        assert api.post(PREPARE_URL, body, format="json").json()["error"] == CANCELLED

    def test_ip_whitelist(self, api, settings, paid_order, pending_payment,
                          click_prepare_body):
        settings.CLICK_ALLOWED_IPS = ["213.230.106.0/24"]
        body = click_prepare_body(paid_order.id, 250000)
        r = api.post(PREPARE_URL, body, format="json", REMOTE_ADDR="8.8.8.8")
        assert r.json()["error"] == SIGN_ERROR


# =====================================================================
# Complete
# =====================================================================
class TestClickComplete:
    def test_muvaffaqiyatli(self, api, paid_order, pending_payment,
                            click_complete_body):
        body = click_complete_body(paid_order.id, pending_payment.id, 250000)
        r = api.post(COMPLETE_URL, body, format="json")
        assert r.json()["error"] == OK

        pending_payment.refresh_from_db()
        paid_order.refresh_from_db()
        assert pending_payment.status == PaymentState.PAID
        assert pending_payment.transaction_id == "1001"
        assert paid_order.payment_status == "paid"

    def test_soxta_prepare_id(self, api, paid_order, pending_payment,
                              click_complete_body):
        """⚠️ Ilgari prepare bosqichisiz to'g'ridan-to'g'ri to'lov o'tardi."""
        body = click_complete_body(paid_order.id, 999999, 250000)
        assert api.post(COMPLETE_URL, body,
                        format="json").json()["error"] == TRANSACTION_NOT_FOUND
        pending_payment.refresh_from_db()
        assert pending_payment.status == PaymentState.PENDING

    def test_boshqa_buyurtmaning_prepare_id_si(self, api, paid_order,
                                               pending_payment, tariff,
                                               click_complete_body):
        boshqa = PaymentFactory(order=OrderFactory(tariff=tariff), amount=250_000)
        body = click_complete_body(paid_order.id, boshqa.id, 250000)
        assert api.post(COMPLETE_URL, body,
                        format="json").json()["error"] == TRANSACTION_NOT_FOUND

    def test_summa_completeda_ham_tekshiriladi(self, api, paid_order,
                                               pending_payment,
                                               click_complete_body):
        body = click_complete_body(paid_order.id, pending_payment.id, 100)
        assert api.post(COMPLETE_URL, body,
                        format="json").json()["error"] == INVALID_AMOUNT

    def test_takroriy_webhook(self, api, paid_order, pending_payment,
                              click_complete_body):
        body = click_complete_body(paid_order.id, pending_payment.id, 250000)
        assert api.post(COMPLETE_URL, body, format="json").json()["error"] == OK
        assert api.post(COMPLETE_URL, body,
                        format="json").json()["error"] == ALREADY_PAID

    def test_click_bekor_qilgan(self, api, paid_order, pending_payment,
                                click_complete_body):
        body = click_complete_body(paid_order.id, pending_payment.id, 250000,
                                   error="-9")
        assert api.post(COMPLETE_URL, body, format="json").json()["error"] == OK
        pending_payment.refresh_from_db()
        assert pending_payment.status == PaymentState.CANCELLED

    def test_soxta_imzo(self, api, paid_order, pending_payment,
                        click_complete_body):
        body = click_complete_body(paid_order.id, pending_payment.id, 250000)
        body["sign_string"] = "yolgon"
        assert api.post(COMPLETE_URL, body,
                        format="json").json()["error"] == SIGN_ERROR
        paid_order.refresh_from_db()
        assert paid_order.payment_status != "paid"

    def test_tolangandan_keyin_bekor_qilish_holatni_buzmaydi(
        self, api, paid_order, pending_payment, click_complete_body
    ):
        ok_body = click_complete_body(paid_order.id, pending_payment.id, 250000)
        api.post(COMPLETE_URL, ok_body, format="json")
        cancel_body = click_complete_body(paid_order.id, pending_payment.id,
                                          250000, trans_id="2002", error="-9")
        api.post(COMPLETE_URL, cancel_body, format="json")
        pending_payment.refresh_from_db()
        assert pending_payment.status == PaymentState.PAID
