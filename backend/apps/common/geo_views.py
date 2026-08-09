"""Geocoding proxy — Yandex API kaliti brauzerga chiqmasligi uchun.

Kalitni frontend'ga qo'yib bo'lmaydi: uni o'g'irlab, sizning hisobingizdan
so'rov yog'dirishadi. Shuning uchun so'rov backend orqali o'tadi.

Natijalar keshlanadi — bir xil manzil qayta-qayta so'raladi va Yandex
so'rovlari pullik/limitli.
"""
import hashlib

from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.responses import error_response, success_response
from apps.common.validators import LatitudeField, LongitudeField
from services.map import map_service


class GeocodeQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=200)


class ReverseGeocodeQuerySerializer(serializers.Serializer):
    lat = LatitudeField()
    lng = LongitudeField()


def cache_key(prefix, value):
    return f"geocode:{prefix}:{hashlib.md5(str(value).encode()).hexdigest()}"


class GeocodeView(APIView):
    """GET /api/geocode/?q=Chilonzor 5-kvartal"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "geocode"

    def get(self, request):
        serializer = GeocodeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["q"].strip()

        key = cache_key("fwd", query.lower())
        natija = cache.get(key)

        if natija is None:
            natija = map_service.geocode(query)
            if natija is None:
                return error_response("Manzil topilmadi", status=404)
            cache.set(key, natija, settings.GEOCODE_CACHE_SECONDS)

        return success_response(data=natija)


class ReverseGeocodeView(APIView):
    """GET /api/geocode/reverse/?lat=41.31&lng=69.24"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "geocode"

    def get(self, request):
        serializer = ReverseGeocodeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        lat = round(serializer.validated_data["lat"], 5)
        lng = round(serializer.validated_data["lng"], 5)

        key = cache_key("rev", f"{lat},{lng}")
        manzil = cache.get(key)

        if manzil is None:
            manzil = map_service.reverse_geocode(lat, lng)
            if manzil is None:
                return error_response("Manzil aniqlanmadi", status=404)
            cache.set(key, manzil, settings.GEOCODE_CACHE_SECONDS)

        return success_response(data={"address": manzil, "lat": lat, "lng": lng})
