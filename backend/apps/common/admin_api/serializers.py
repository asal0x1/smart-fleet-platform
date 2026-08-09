"""Admin panel uchun serializerlar.

Mijoz/haydovchi serializerlaridan alohida saqlanadi, chunki admin
ko'proq maydon ko'radi (is_active, is_staff, telefon raqamlar, h.k.).
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.drivers.models import Driver
from apps.orders.models import Order, Tariff
from apps.payments.models import Payment
from apps.requests.models import (
    HeavyEquipmentRequest,
    RequestStatus,
    WeddingRequest,
)
from apps.users.models import User


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
class AdminUserSerializer(serializers.ModelSerializer):
    """Foydalanuvchilar ro'yxati (admin ko'rinishi)."""

    orders_count = serializers.IntegerField(read_only=True, default=0)
    is_driver = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "phone", "full_name", "email", "role", "avatar_url",
            "is_active", "is_verified", "is_staff", "is_driver",
            "orders_count", "last_login", "created_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.BooleanField())
    def get_is_driver(self, obj):
        return hasattr(obj, "driver")


# ---------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------
class AdminDriverSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    user_is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    lat = serializers.FloatField(source="current_lat", read_only=True)
    lng = serializers.FloatField(source="current_lng", read_only=True)
    orders_count = serializers.IntegerField(read_only=True, default=0)
    missing_documents = serializers.SerializerMethodField()
    documents_complete = serializers.BooleanField(
        source="has_documents", read_only=True
    )

    class Meta:
        model = Driver
        fields = [
            "id", "user_id", "full_name", "phone", "user_is_active",
            "car_model", "car_color", "car_number", "license_number",
            "is_active", "is_online", "rating", "total_trips",
            "orders_count", "lat", "lng",
            "license_photo", "tech_passport_photo", "passport_photo",
            "car_photo", "missing_documents", "documents_complete",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_missing_documents(self, obj):
        return obj.missing_documents


class AdminDriverUpdateSerializer(serializers.ModelSerializer):
    """Admin haydovchi ma'lumotlarini tahrirlashi uchun."""

    class Meta:
        model = Driver
        fields = ["car_model", "car_color", "car_number", "license_number"]


# ---------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------
class AdminOrderSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()
    tariff_name = serializers.CharField(source="tariff.name", read_only=True)
    from_lat = serializers.FloatField(read_only=True)
    from_lng = serializers.FloatField(read_only=True)
    to_lat = serializers.FloatField(read_only=True)
    to_lng = serializers.FloatField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "status", "client", "driver", "tariff_name",
            "from_address", "from_lat", "from_lng",
            "to_address", "to_lat", "to_lng",
            "estimated_price", "final_price", "distance_km", "duration_min",
            "payment_method", "payment_status", "cancel_reason",
            "created_at", "accepted_at", "started_at", "completed_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_client(self, obj):
        if obj.client_id is None:
            return None
        return {
            "id": obj.client_id,
            "full_name": obj.client.full_name,
            "phone": obj.client.phone,
        }

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_driver(self, obj):
        if obj.driver_id is None:
            return None
        return {
            "id": obj.driver_id,
            "full_name": obj.driver.user.full_name,
            "phone": obj.driver.user.phone,
            "car_model": obj.driver.car_model,
            "car_number": obj.driver.car_number,
            "rating": float(obj.driver.rating),
        }


class AdminCancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AdminAssignDriverSerializer(serializers.Serializer):
    driver_id = serializers.IntegerField()


# ---------------------------------------------------------------------
# Tariffs (to'liq CRUD)
# ---------------------------------------------------------------------
class AdminTariffSerializer(serializers.ModelSerializer):
    orders_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tariff
        fields = [
            "id", "name", "name_uz", "base_fare", "per_km", "per_minute",
            "minimum_fare", "icon_url", "is_active", "orders_count",
        ]
        read_only_fields = ["id", "orders_count"]

    def validate(self, attrs):
        base = attrs.get("base_fare", getattr(self.instance, "base_fare", 0))
        minimum = attrs.get("minimum_fare", getattr(self.instance, "minimum_fare", 0))
        if minimum < base:
            raise serializers.ValidationError(
                {"minimum_fare": "Minimal narx boshlang'ich narxdan kichik bo'lmasligi kerak"}
            )
        return attrs


# ---------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------
class AdminPaymentSerializer(serializers.ModelSerializer):
    order_status = serializers.CharField(source="order.status", read_only=True)
    client_phone = serializers.CharField(source="order.client.phone", read_only=True)
    client_name = serializers.CharField(source="order.client.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "order_id", "order_status", "client_name", "client_phone",
            "amount", "method", "status", "transaction_id",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------
# Requests (og'ir texnika + to'y)
# ---------------------------------------------------------------------
class AdminHeavyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeavyEquipmentRequest
        fields = [
            "id", "category", "items", "address", "lat", "lng",
            "start_date", "start_time", "duration_days",
            "contact_name", "contact_phone", "notes", "status",
            "estimated_price", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminWeddingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeddingRequest
        fields = [
            "id", "car_brand", "car_count", "decoration_type", "address",
            "date", "time", "duration_hours",
            "contact_name", "contact_phone", "notes",
            "estimated_price", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RequestStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=RequestStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


# ---------------------------------------------------------------------
# Umumiy action serializerlari
# ---------------------------------------------------------------------
class BlockSerializer(serializers.Serializer):
    """is_active=False qilish yoki qaytarish."""

    is_active = serializers.BooleanField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
