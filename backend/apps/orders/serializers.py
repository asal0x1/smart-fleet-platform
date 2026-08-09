from rest_framework import serializers

from apps.common.validators import LatitudeField, LongitudeField

from .models import Order, Review, Tariff


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = [
            "id", "name", "name_uz", "base_fare", "per_km",
            "per_minute", "minimum_fare", "icon_url",
        ]


class CreateOrderSerializer(serializers.Serializer):
    from_address = serializers.CharField(max_length=255)
    from_lat = LatitudeField()
    from_lng = LongitudeField()
    to_address = serializers.CharField(max_length=255)
    to_lat = LatitudeField()
    to_lng = LongitudeField()
    tariff_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=["cash", "click", "payme"], default="cash"
    )


class EstimateSerializer(serializers.Serializer):
    from_lat = LatitudeField()
    from_lng = LongitudeField()
    to_lat = LatitudeField()
    to_lng = LongitudeField()
    tariff_id = serializers.IntegerField()


class DriverInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="user.full_name")
    car = serializers.CharField(source="car_model")
    car_number = serializers.CharField()
    rating = serializers.DecimalField(max_digits=2, decimal_places=1)


class OrderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    from_lat = serializers.FloatField(read_only=True)
    from_lng = serializers.FloatField(read_only=True)
    to_lat = serializers.FloatField(read_only=True)
    to_lng = serializers.FloatField(read_only=True)
    tariff_name = serializers.CharField(source="tariff.name", read_only=True)
    driver = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "client_name", "status",
            "from_address", "from_lat", "from_lng",
            "to_address", "to_lat", "to_lng",
            "tariff_name", "estimated_price", "final_price",
            "distance_km", "duration_min",
            "payment_method", "payment_status",
            "driver", "created_at", "accepted_at", "completed_at",
        ]

    def get_driver(self, obj):
        if obj.driver is None:
            return None
        return {
            "id": obj.driver.id,
            "name": obj.driver.user.full_name,
            "car": obj.driver.car_model,
            "car_number": obj.driver.car_number,
            "rating": float(obj.driver.rating),
        }


class ChangeStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            "accepted", "driver_arrived", "ongoing", "completed", "cancelled",
        ]
    )
    # Haydovchi ilovasi o'lchagan haqiqiy masofa (completed uchun)
    actual_distance_km = serializers.FloatField(
        required=False, min_value=0, max_value=2000
    )


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "order", "author_name", "kind", "rating", "comment",
                  "created_at"]
        read_only_fields = fields


class CreateReviewSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=1000, required=False,
                                    allow_blank=True)
