from django.contrib.gis.geos import Point
from rest_framework import serializers

from apps.common.validators import LatitudeField, LongitudeField

from .models import Driver


class DriverProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    current_lat = serializers.FloatField(read_only=True)
    current_lng = serializers.FloatField(read_only=True)
    missing_documents = serializers.SerializerMethodField()
    documents_complete = serializers.BooleanField(
        source="has_documents", read_only=True
    )

    class Meta:
        model = Driver
        fields = [
            "id", "full_name", "phone",
            "car_model", "car_color", "car_number", "license_number",
            "is_active", "is_online", "rating", "total_trips",
            "current_lat", "current_lng",
            "license_photo", "tech_passport_photo", "passport_photo",
            "car_photo", "missing_documents", "documents_complete",
        ]
        read_only_fields = [
            "id", "is_active", "rating", "total_trips",
            "license_photo", "tech_passport_photo", "passport_photo",
            "car_photo",
        ]

    def get_missing_documents(self, obj):
        return obj.missing_documents


class LocationUpdateSerializer(serializers.Serializer):
    lat = LatitudeField()
    lng = LongitudeField()
    accuracy = serializers.FloatField(required=False, min_value=0)

    def save(self, driver):
        lat = self.validated_data["lat"]
        lng = self.validated_data["lng"]
        driver.location = Point(lng, lat, srid=4326)
        driver.save(update_fields=["location", "updated_at"])
        return driver


class OnlineStatusSerializer(serializers.Serializer):
    is_online = serializers.BooleanField()


class NearbyDriverSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.full_name", read_only=True)
    lat = serializers.FloatField(source="current_lat", read_only=True)
    lng = serializers.FloatField(source="current_lng", read_only=True)
    distance_m = serializers.SerializerMethodField()
    eta_min = serializers.SerializerMethodField()
    car = serializers.CharField(source="car_model", read_only=True)

    class Meta:
        model = Driver
        fields = ["id", "name", "lat", "lng", "distance_m", "eta_min", "car", "rating"]

    def get_distance_m(self, obj):
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.m)
        return None

    def get_eta_min(self, obj):
        # ~ shahar tezligi 40 km/soat = 667 m/min
        if hasattr(obj, "distance") and obj.distance is not None:
            return max(1, round(obj.distance.m / 667))
        return None


class NearbyQuerySerializer(serializers.Serializer):
    """`nearby/?lat=&lng=&radius=` parametrlarini tekshiradi.

    radius chegarasi muhim: chegarasiz `?radius=99999999` butun bazani
    PostGIS orqali skanerlab, serverni qotirib qo'yishi mumkin.
    """

    lat = LatitudeField()
    lng = LongitudeField()
    radius = serializers.IntegerField(
        required=False, default=5000, min_value=100, max_value=50_000
    )
    limit = serializers.IntegerField(
        required=False, default=10, min_value=1, max_value=50
    )


class DriverDocumentsSerializer(serializers.ModelSerializer):
    """Hujjat rasmlarini yuklash (multipart/form-data)."""

    missing_documents = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source="has_documents", read_only=True)

    class Meta:
        model = Driver
        fields = [
            "license_photo", "tech_passport_photo", "passport_photo",
            "car_photo", "missing_documents", "is_complete",
        ]

    def get_missing_documents(self, obj):
        return obj.missing_documents

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Kamida bitta hujjat rasmi yuborilishi kerak"
            )
        return attrs

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Hujjat almashtirilsa tasdiqni qayta ko'rib chiqish kerak
        if instance.is_active and not instance.has_documents:
            instance.is_active = False
            instance.save(update_fields=["is_active", "updated_at"])
        return instance
