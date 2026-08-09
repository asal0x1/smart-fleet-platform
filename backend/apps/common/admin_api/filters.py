"""django-filter FilterSet'lari — admin ro'yxatlarini filtrlash uchun.

Sanalar `?created_from=2026-01-01&created_to=2026-01-31` ko'rinishida
beriladi (ikkalasi ham inklyuziv).
"""
import django_filters as df

from apps.drivers.models import Driver
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.requests.models import HeavyEquipmentRequest, WeddingRequest
from apps.users.models import User


class UserFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = User
        fields = ["role", "is_active", "is_verified", "is_staff"]


class DriverFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")
    rating_min = df.NumberFilter(field_name="rating", lookup_expr="gte")
    has_location = df.BooleanFilter(
        field_name="location", lookup_expr="isnull", exclude=True
    )

    class Meta:
        model = Driver
        fields = ["is_active", "is_online"]


class OrderFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")
    price_min = df.NumberFilter(field_name="estimated_price", lookup_expr="gte")
    price_max = df.NumberFilter(field_name="estimated_price", lookup_expr="lte")
    client_id = df.NumberFilter(field_name="client_id")
    driver_id = df.NumberFilter(field_name="driver_id")
    tariff_id = df.NumberFilter(field_name="tariff_id")
    no_driver = df.BooleanFilter(field_name="driver", lookup_expr="isnull")

    class Meta:
        model = Order
        fields = ["status", "payment_status", "payment_method"]


class PaymentFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")
    amount_min = df.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = df.NumberFilter(field_name="amount", lookup_expr="lte")
    order_id = df.NumberFilter(field_name="order_id")

    class Meta:
        model = Payment
        fields = ["status", "method"]


class HeavyRequestFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")
    start_from = df.DateFilter(field_name="start_date", lookup_expr="gte")
    start_to = df.DateFilter(field_name="start_date", lookup_expr="lte")

    class Meta:
        model = HeavyEquipmentRequest
        fields = ["status", "category"]


class WeddingRequestFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = WeddingRequest
        fields = ["status", "decoration_type"]
