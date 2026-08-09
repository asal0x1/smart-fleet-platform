"""
Xarita servislari:
  - Yandex Maps: manzil -> koordinata (geocoding) va teskarisi (kalit bo'lsa)
  - Nominatim (OpenStreetMap): Yandex kaliti yo'q bo'lganda bepul zaxira
  - OSRM: ikki nuqta orasidagi masofa va vaqt (route)
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Nominatim foydalanish siyosati o'ziga xos User-Agent talab qiladi —
# standart "python-requests/..." headeri bilan so'rovlar rad etilishi mumkin.
NOMINATIM_HEADERS = {"User-Agent": "SmartFleet-App/1.0 (operator@smartfleet.uz)"}
NOMINATIM_URL = "https://nominatim.openstreetmap.org"

# Toshkent shahri atrofidagi taxminiy chegara (viewbox: chap,yuqori,o'ng,past).
# Xizmat hozircha faqat Toshkent shahri bo'ylab ishlaydi, shuning uchun
# qidiruv natijalari boshqa viloyatlarga chiqib ketmasligi uchun shu
# chegara bilan qattiq cheklanadi (bounded=1).
TASHKENT_VIEWBOX = "69.05,41.42,69.45,41.18"


class MapService:
    def __init__(self):
        self.yandex_key = settings.YANDEX_MAPS_API_KEY
        self.osrm_url = settings.OSRM_BASE_URL

    # --- Geocoding (Yandex bo'lsa shu, bo'lmasa Nominatim) ---

    def geocode(self, address):
        """Manzil -> {address, lat, lng}. Topilmasa None."""
        if self.yandex_key:
            result = self._yandex_geocode(address)
            if result is not None:
                return result
        return self._nominatim_geocode(address)

    def reverse_geocode(self, lat, lng):
        """Koordinata -> manzil (str) yoki None."""
        if self.yandex_key:
            result = self._yandex_reverse_geocode(lat, lng)
            if result is not None:
                return result
        return self._nominatim_reverse_geocode(lat, lng)

    # --- Yandex ---

    def _yandex_geocode(self, address):
        try:
            resp = requests.get(
                "https://geocode-maps.yandex.ru/1.x/",
                params={
                    "format": "json",
                    "geocode": address,
                    "apikey": self.yandex_key,
                },
                timeout=10,
            )
            resp.raise_for_status()
            members = resp.json()["response"]["GeoObjectCollection"]["featureMember"]
            if not members:
                return None
            obj = members[0]["GeoObject"]
            lng, lat = map(float, obj["Point"]["pos"].split())
            return {"address": obj["name"], "lat": lat, "lng": lng}
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.error("Yandex geocode xatosi: %s", exc)
            return None

    def _yandex_reverse_geocode(self, lat, lng):
        try:
            resp = requests.get(
                "https://geocode-maps.yandex.ru/1.x/",
                params={
                    "format": "json",
                    "geocode": f"{lng},{lat}",
                    "apikey": self.yandex_key,
                },
                timeout=10,
            )
            resp.raise_for_status()
            members = resp.json()["response"]["GeoObjectCollection"]["featureMember"]
            return members[0]["GeoObject"]["name"] if members else None
        except (requests.RequestException, KeyError, IndexError) as exc:
            logger.error("Yandex reverse geocode xatosi: %s", exc)
            return None

    # --- Nominatim (OpenStreetMap, kalit shart emas) ---

    def _nominatim_geocode(self, address):
        # 1-bosqich: Toshkent ichida qat'iy qidiruv (tez va aniq, lekin
        # ba'zi ko'cha nomlarini topa olmasligi mumkin — Nominatim'ning
        # bounded rejimi ba'zan haddan tashqari qattiq bo'ladi).
        result = self._nominatim_search(address, bounded=True, limit=1)
        if result is not None:
            return result

        # 2-bosqich: kengroq qidiruv, lekin natija Toshkent chegarasidan
        # tashqarida bo'lsa rad etiladi — shu bilan boshqa viloyatlardagi
        # bir xil nomli ko'chalar hech qachon qaytmaydi.
        candidates = self._nominatim_search(address, bounded=False, limit=5, many=True)
        for candidate in candidates or []:
            if self._within_tashkent(candidate["lat"], candidate["lng"]):
                return candidate
        return None

    def _nominatim_search(self, address, bounded, limit, many=False):
        try:
            params = {
                "q": address,
                "format": "jsonv2",
                "limit": limit,
                "countrycodes": "uz",
                "addressdetails": 0,
            }
            if bounded:
                params["viewbox"] = TASHKENT_VIEWBOX
                params["bounded"] = 1
            resp = requests.get(
                f"{NOMINATIM_URL}/search", params=params,
                headers=NOMINATIM_HEADERS, timeout=10,
            )
            resp.raise_for_status()
            results = resp.json()
            parsed = [
                {
                    "address": r["display_name"],
                    "lat": float(r["lat"]),
                    "lng": float(r["lon"]),
                }
                for r in results
            ]
            if many:
                return parsed
            return parsed[0] if parsed else None
        except (requests.RequestException, KeyError, ValueError, IndexError) as exc:
            logger.error("Nominatim geocode xatosi: %s", exc)
            return [] if many else None

    @staticmethod
    def _within_tashkent(lat, lng):
        min_lng, max_lat, max_lng, min_lat = (float(v) for v in TASHKENT_VIEWBOX.split(","))
        return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng

    def _nominatim_reverse_geocode(self, lat, lng):
        try:
            resp = requests.get(
                f"{NOMINATIM_URL}/reverse",
                params={"lat": lat, "lon": lng, "format": "jsonv2"},
                headers=NOMINATIM_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("display_name")
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.error("Nominatim reverse geocode xatosi: %s", exc)
            return None

    # --- OSRM route ---

    def route(self, from_lat, from_lng, to_lat, to_lng):
        """
        Ikki nuqta orasidagi yo'l -> {distance_km, duration_min}.
        Xato bo'lsa haversine bilan taxminiy hisoblaydi.
        """
        try:
            url = (
                f"{self.osrm_url}/route/v1/driving/"
                f"{from_lng},{from_lat};{to_lng},{to_lat}"
            )
            resp = requests.get(url, params={"overview": "false"}, timeout=10)
            resp.raise_for_status()
            route = resp.json()["routes"][0]
            return {
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_min": max(1, round(route["duration"] / 60)),
            }
        except (requests.RequestException, KeyError, IndexError) as exc:
            logger.warning("OSRM xatosi, haversine ishlatilmoqda: %s", exc)
            return self._haversine_fallback(from_lat, from_lng, to_lat, to_lng)

    @staticmethod
    def _haversine_fallback(from_lat, from_lng, to_lat, to_lng):
        import math

        r = 6371  # km
        d_lat = math.radians(to_lat - from_lat)
        d_lng = math.radians(to_lng - from_lng)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(from_lat))
            * math.cos(math.radians(to_lat))
            * math.sin(d_lng / 2) ** 2
        )
        dist_km = round(r * 2 * math.asin(math.sqrt(a)) * 1.3, 2)  # 1.3 = yo'l egriligi
        return {"distance_km": dist_km, "duration_min": max(1, round(dist_km / 0.5))}


map_service = MapService()
