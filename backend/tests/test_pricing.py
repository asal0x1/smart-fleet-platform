"""Narx hisoblash va OSRM/haversine mantiqidagi testlar."""
import pytest

from apps.orders.services import estimate_order
from services.map import MapService, map_service
from tests.conftest import data_of
from tests.factories import TariffFactory


class TestCalculatePrice:
    def test_oddiy_hisob(self, db):
        t = TariffFactory(base_fare=5000, per_km=2000, per_minute=500,
                          minimum_fare=10000)
        # 5000 + 2000*10 + 500*20 = 35000
        assert t.calculate_price(10, 20) == 35000

    def test_minimal_narxdan_past_tushmaydi(self, db):
        t = TariffFactory(base_fare=3000, per_km=1000, per_minute=100,
                          minimum_fare=15000)
        # 3000 + 1000*1 + 100*2 = 4200 -> minimum_fare
        assert t.calculate_price(1, 2) == 15000

    def test_kasr_masofa_yaxlitlanadi(self, db):
        t = TariffFactory(base_fare=0, per_km=1000, per_minute=0, minimum_fare=0)
        assert t.calculate_price(3.456, 0) == 3456

    def test_nol_masofa(self, db):
        t = TariffFactory(base_fare=5000, per_km=2000, per_minute=500,
                          minimum_fare=8000)
        assert t.calculate_price(0, 0) == 8000


class TestHaversineFallback:
    def test_masofa_maqbul_oraliqda(self):
        # Chilonzor -> Yunusobod, to'g'ri chiziqda ~9 km, 1.3 koeffitsiyent bilan ~12
        r = MapService._haversine_fallback(41.2856, 69.2034, 41.3600, 69.2890)
        assert 8 < r["distance_km"] < 16
        assert r["duration_min"] >= 1

    def test_bir_xil_nuqta_nol_masofa(self):
        r = MapService._haversine_fallback(41.31, 69.24, 41.31, 69.24)
        assert r["distance_km"] == 0
        assert r["duration_min"] == 1  # max(1, ...)

    def test_simmetrik(self):
        a = MapService._haversine_fallback(41.28, 69.20, 41.36, 69.28)
        b = MapService._haversine_fallback(41.36, 69.28, 41.28, 69.20)
        assert a == b

    def test_tarmoq_yoq_boganda_route_fallbackga_otadi(self):
        """block_network fixture'i requests.get ni bloklaydi."""
        r = map_service.route(41.2856, 69.2034, 41.3600, 69.2890)
        assert r["distance_km"] > 0
        assert "duration_min" in r


class TestOSRMMuvaffaqiyatli:
    def test_osrm_javobi_ishlatiladi(self, monkeypatch):
        class FakeResp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"routes": [{"distance": 12345, "duration": 900}]}

        monkeypatch.setattr("services.map.requests.get", lambda *a, **k: FakeResp())
        r = map_service.route(41.28, 69.20, 41.36, 69.28)
        assert r == {"distance_km": 12.35, "duration_min": 15}


class TestEstimateEndpoint:
    def test_estimate_narx_qaytaradi(self, auth_as, client_user, tariff):
        c = auth_as(client_user)
        r = c.post("/api/orders/estimate/", {
            "from_lat": 41.2856, "from_lng": 69.2034,
            "to_lat": 41.3600, "to_lng": 69.2890,
            "tariff_id": tariff.id,
        }, format="json")
        assert r.status_code == 200
        d = data_of(r)
        assert d["estimated_price"] > 0
        assert d["distance_km"] > 0

    def test_notogri_tarif(self, auth_as, client_user):
        c = auth_as(client_user)
        r = c.post("/api/orders/estimate/", {
            "from_lat": 41.28, "from_lng": 69.20,
            "to_lat": 41.36, "to_lng": 69.28, "tariff_id": 999999,
        }, format="json")
        assert r.status_code == 404

    @pytest.mark.parametrize("field,value", [
        ("from_lat", 100), ("to_lng", -200), ("from_lng", 181),
    ])
    def test_notogri_koordinata(self, auth_as, client_user, tariff, field, value):
        c = auth_as(client_user)
        payload = {"from_lat": 41.28, "from_lng": 69.20, "to_lat": 41.36,
                   "to_lng": 69.28, "tariff_id": tariff.id}
        payload[field] = value
        assert c.post("/api/orders/estimate/", payload, format="json").status_code == 400

    def test_token_yoq(self, api, tariff):
        r = api.post("/api/orders/estimate/", {}, format="json")
        assert r.status_code == 401


class TestEskizToken:
    """Token endi cache'da — ko'p worker'da ham bitta token ishlatiladi."""

    def test_token_keshlanadi(self, monkeypatch):
        from django.core.cache import cache

        from services.sms import TOKEN_CACHE_KEY, EskizSMSService

        cache.delete(TOKEN_CACHE_KEY)
        chaqiruvlar = []

        class FakeResp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {"data": {"token": "abc123"}}

        def fake_post(*args, **kwargs):
            chaqiruvlar.append(args)
            return FakeResp()

        monkeypatch.setattr("services.sms.requests.post", fake_post)

        svc = EskizSMSService()
        assert svc._get_token() == "abc123"
        # Ikkinchi marta cache'dan olinadi -> yangi login so'rovi yo'q
        assert svc._get_token() == "abc123"
        assert len(chaqiruvlar) == 1

        # Boshqa "worker" ham bir xil tokenni ko'radi
        assert EskizSMSService()._get_token() == "abc123"
        assert len(chaqiruvlar) == 1
        cache.delete(TOKEN_CACHE_KEY)
