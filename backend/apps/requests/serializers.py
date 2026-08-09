from rest_framework import serializers

from apps.common.validators import LatitudeField, LongitudeField, PhoneField

from .models import (
    BusRequest,
    GiftMemorialRequest,
    HeavyEquipmentRequest,
    PersonalDriverRequest,
    WeddingRequest,
)


class HeavyItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)


class HeavyEquipmentRequestSerializer(serializers.ModelSerializer):
    items = HeavyItemSerializer(many=True)
    contact_phone = PhoneField()
    lat = LatitudeField(required=False, allow_null=True)
    lng = LongitudeField(required=False, allow_null=True)

    class Meta:
        model = HeavyEquipmentRequest
        fields = [
            "id", "category", "items", "address", "lat", "lng",
            "start_date", "start_time", "duration_days",
            "contact_name", "contact_phone", "notes", "status", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class WeddingRequestSerializer(serializers.ModelSerializer):
    contact_phone = PhoneField()

    class Meta:
        model = WeddingRequest
        fields = [
            "id", "car_brand", "car_count", "decoration_type", "address",
            "date", "time", "duration_hours",
            "contact_name", "contact_phone", "notes",
            "estimated_price", "status", "created_at",
        ]
        read_only_fields = ["id", "estimated_price", "status", "created_at"]


class PersonalDriverRequestSerializer(serializers.ModelSerializer):
    contact_phone = PhoneField()

    class Meta:
        model = PersonalDriverRequest
        fields = [
            "id", "car_brand", "driver_experience", "contract_duration",
            "address", "start_date",
            "contact_name", "contact_phone", "notes",
            "estimated_price", "status", "created_at",
        ]
        read_only_fields = ["id", "estimated_price", "status", "created_at"]


class BusRequestSerializer(serializers.ModelSerializer):
    contact_phone = PhoneField()

    class Meta:
        model = BusRequest
        fields = [
            "id", "category", "bus_brand", "bus_count", "address",
            "date", "time", "duration_hours",
            "contact_name", "contact_phone", "notes",
            "estimated_price", "status", "created_at",
        ]
        read_only_fields = ["id", "estimated_price", "status", "created_at"]


class GiftMemorialRequestSerializer(serializers.ModelSerializer):
    contact_phone = PhoneField()

    class Meta:
        model = GiftMemorialRequest
        fields = [
            "id", "kind", "decoration_type", "address", "date", "time",
            "contact_name", "contact_phone", "notes",
            "estimated_price", "status", "created_at",
        ]
        read_only_fields = ["id", "estimated_price", "status", "created_at"]
