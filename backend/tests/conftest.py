"""Umumiy pytest fixture'lari.

Eng muhimi — `block_network`: testlar hech qachon haqiqiy OSRM, Yandex
yoki Eskiz serveriga chiqmasligi kerak. Ilgari loyihada test yo'q edi,
lekin manual tekshiruvlar ham real OSRM'ga so'rov yuborardi va u 403
qaytarganda natijalar tushunarsiz bo'lib qolardi.
"""
import hashlib

import pytest
import requests
from django.core.cache import cache
from rest_framework.test import APIClient

from tests.factories import (  # noqa: F401  (fixture'larda ishlatiladi)
    TEST_PASSWORD,
    AdminFactory,
    ClientFactory,
    DriverFactory,
    DriverUserFactory,
    OrderFactory,
    TariffFactory,
    UnapprovedDriverFactory,
)


# =====================================================================
# Tashqi olamni yopish
# =====================================================================
class NetworkBlocked(requests.RequestException):
    """Testda tarmoqqa chiqishga urinildi."""


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """requests orqali har qanday tashqi so'rovni bloklaydi.

    MapService.route() bu xatoni ushlab haversine fallback'ga o'tadi,
    ya'ni testlarda masofa deterministik hisoblanadi.
    """

    def blocked(*args, **kwargs):
        raise NetworkBlocked("Testda tashqi tarmoq bloklangan")

    monkeypatch.setattr(requests, "get", blocked)
    monkeypatch.setattr(requests, "post", blocked)
    monkeypatch.setattr("services.map.requests.get", blocked)
    monkeypatch.setattr("services.sms.requests.post", blocked)


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Throttle hisoblagichlari testlar orasida oqib ketmasin."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def throttle_rate(monkeypatch):
    """Test ichida throttle cheklovini o'zgartiradi.

    `settings.REST_FRAMEWORK` ni o'zgartirish YETARLI EMAS:
    `SimpleRateThrottle.THROTTLE_RATES` sinf yaratilish paytida
    `api_settings.DEFAULT_THROTTLE_RATES` ga havola sifatida olinadi.
    `api_settings.reload()` yangi dict yasaydi, sinf esa eskisiga
    ishora qilib qolaveradi. Shuning uchun to'g'ridan-to'g'ri sinf
    atributini almashtiramiz.
    """
    from rest_framework.throttling import SimpleRateThrottle

    def _set(scope, rate):
        rates = dict(SimpleRateThrottle.THROTTLE_RATES)
        rates[scope] = rate
        monkeypatch.setattr(SimpleRateThrottle, "THROTTLE_RATES", rates)

    return _set


# =====================================================================
# HTTP klientlar
# =====================================================================
@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def auth_as():
    """`auth_as(user)` -> shu user nomidan ishlaydigan APIClient."""
    from apps.users.serializers import tokens_for_user

    def _make(user):
        client = APIClient()
        token = tokens_for_user(user)["access_token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return _make


# =====================================================================
# Obyektlar
# =====================================================================
@pytest.fixture
def password():
    return TEST_PASSWORD


@pytest.fixture
def tariff(db):
    return TariffFactory()


@pytest.fixture
def client_user(db):
    return ClientFactory()


@pytest.fixture
def other_client(db):
    return ClientFactory()


@pytest.fixture
def driver(db):
    """Tasdiqlangan haydovchi."""
    return DriverFactory()


@pytest.fixture
def driver2(db):
    return DriverFactory()


@pytest.fixture
def unapproved_driver(db):
    return UnapprovedDriverFactory()


@pytest.fixture
def admin_user(db):
    return AdminFactory()


@pytest.fixture
def order(db, client_user, tariff):
    return OrderFactory(client=client_user, tariff=tariff)


# =====================================================================
# Yordamchilar
# =====================================================================
@pytest.fixture
def click_sign(settings):
    """Click webhook uchun to'g'ri MD5 imzo yasaydi."""

    def _sign(*parts):
        raw = "".join(str(p) for p in parts)
        return hashlib.md5(raw.encode()).hexdigest()

    return _sign


@pytest.fixture
def click_prepare_body(settings, click_sign):
    def _make(order_id, amount, trans_id="1001", sign_time="2026-08-06 10:00:00"):
        body = {
            "click_trans_id": trans_id,
            "service_id": settings.CLICK_SERVICE_ID,
            "merchant_trans_id": str(order_id),
            "amount": str(amount),
            "action": "0",
            "sign_time": sign_time,
        }
        body["sign_string"] = click_sign(
            trans_id, settings.CLICK_SERVICE_ID, settings.CLICK_SECRET_KEY,
            order_id, amount, "0", sign_time,
        )
        return body

    return _make


@pytest.fixture
def click_complete_body(settings, click_sign):
    def _make(order_id, prepare_id, amount, trans_id="1001", error="0",
              sign_time="2026-08-06 10:00:00"):
        body = {
            "click_trans_id": trans_id,
            "service_id": settings.CLICK_SERVICE_ID,
            "merchant_trans_id": str(order_id),
            "merchant_prepare_id": str(prepare_id),
            "amount": str(amount),
            "action": "1",
            "error": error,
            "sign_time": sign_time,
        }
        body["sign_string"] = click_sign(
            trans_id, settings.CLICK_SERVICE_ID, settings.CLICK_SECRET_KEY,
            order_id, prepare_id, amount, "1", sign_time,
        )
        return body

    return _make


def data_of(response):
    """`{"success": true, "data": ...}` konvertidan `data` ni oladi.

    `available/` va `tariffs/` konvertsiz massiv qaytaradi — shuni ham
    qo'llab-quvvatlaymiz.
    """
    body = response.json()
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body
