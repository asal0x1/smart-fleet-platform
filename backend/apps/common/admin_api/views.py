"""Admin panel (frontend) uchun API view'lari.

Barchasi `IsAdminRole` bilan himoyalangan: role="admin" yoki is_staff=True.
Ro'yxatlar `StandardPagination` ishlatadi -> javob formati:

    {"success": true, "data": {"count": .., "results": [..]}}
"""
import datetime

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from apps.common.permissions import IsAdminRole
from apps.common.responses import error_response, success_response
from apps.drivers.models import Driver
from apps.orders.models import Order, OrderStatus, Tariff
from apps.orders.services import change_status
from apps.payments.models import Payment, PaymentState
from apps.requests.models import HeavyEquipmentRequest, WeddingRequest
from apps.users.models import User

from .filters import (
    DriverFilter,
    HeavyRequestFilter,
    OrderFilter,
    PaymentFilter,
    UserFilter,
    WeddingRequestFilter,
)
from .serializers import (
    AdminAssignDriverSerializer,
    AdminCancelOrderSerializer,
    AdminDriverSerializer,
    AdminDriverUpdateSerializer,
    AdminHeavyRequestSerializer,
    AdminOrderSerializer,
    AdminPaymentSerializer,
    AdminTariffSerializer,
    AdminUserSerializer,
    AdminWeddingRequestSerializer,
    BlockSerializer,
    RequestStatusSerializer,
)


class AdminListView(ListAPIView):
    """Barcha admin ro'yxatlari uchun umumiy asos."""

    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


class AdminAPIView(APIView):
    permission_classes = [IsAdminRole]


def parse_date(value, default=None):
    """'2026-01-31' -> date. Noto'g'ri bo'lsa ValidationError."""
    if not value:
        return default
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError(
            {"date": "Sana formati: YYYY-MM-DD"}
        ) from exc


# =====================================================================
# 1. STATISTIKA
# =====================================================================
class DashboardStatsView(AdminAPIView):
    """GET /api/admin/stats/ — dashboard uchun umumiy raqamlar."""

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def get(self, request):
        today = timezone.localdate()
        week_ago = today - datetime.timedelta(days=7)
        month_start = today.replace(day=1)

        orders_by_status = dict(
            Order.objects.values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        revenue = Order.objects.filter(status=OrderStatus.COMPLETED).aggregate(
            total=Sum("final_price"),
            avg=Avg("final_price"),
        )

        return success_response(
            data={
                "users": {
                    "total": User.objects.filter(role="client").count(),
                    "new_today": User.objects.filter(
                        role="client", created_at__date=today
                    ).count(),
                    "new_this_week": User.objects.filter(
                        role="client", created_at__date__gte=week_ago
                    ).count(),
                    "blocked": User.objects.filter(is_active=False).count(),
                },
                "drivers": {
                    "total": Driver.objects.count(),
                    "approved": Driver.objects.filter(is_active=True).count(),
                    "pending_approval": Driver.objects.filter(is_active=False).count(),
                    "online": Driver.objects.filter(is_online=True).count(),
                },
                "orders": {
                    "total": Order.objects.count(),
                    "today": Order.objects.filter(created_at__date=today).count(),
                    "this_month": Order.objects.filter(
                        created_at__date__gte=month_start
                    ).count(),
                    "completed": orders_by_status.get("completed", 0),
                    "pending": orders_by_status.get("pending", 0),
                    "cancelled": orders_by_status.get("cancelled", 0),
                    "by_status": orders_by_status,
                },
                "revenue": {
                    "total": revenue["total"] or 0,
                    "average_check": round(revenue["avg"] or 0),
                    "today": Order.objects.filter(
                        status=OrderStatus.COMPLETED, completed_at__date=today
                    ).aggregate(t=Sum("final_price"))["t"] or 0,
                    "this_month": Order.objects.filter(
                        status=OrderStatus.COMPLETED,
                        completed_at__date__gte=month_start,
                    ).aggregate(t=Sum("final_price"))["t"] or 0,
                },
                "requests": {
                    "heavy_pending": HeavyEquipmentRequest.objects.filter(
                        status="pending"
                    ).count(),
                    "wedding_pending": WeddingRequest.objects.filter(
                        status="pending"
                    ).count(),
                },
            }
        )


class RevenueStatsView(AdminAPIView):
    """GET /api/admin/stats/revenue/?from=&to=&group_by=day|week|month

    Grafik chizish uchun sana bo'yicha kesilgan daromad.
    """

    TRUNC = {"day": TruncDate, "week": TruncWeek, "month": TruncMonth}

    @extend_schema(
        parameters=[
            OpenApiParameter("from", OpenApiTypes.DATE, description="YYYY-MM-DD"),
            OpenApiParameter("to", OpenApiTypes.DATE, description="YYYY-MM-DD"),
            OpenApiParameter("group_by", enum=["day", "week", "month"]),
        ],
        responses=OpenApiTypes.OBJECT,
        tags=["admin"],
    )
    def get(self, request):
        today = timezone.localdate()
        date_from = parse_date(
            request.query_params.get("from"), today - datetime.timedelta(days=30)
        )
        date_to = parse_date(request.query_params.get("to"), today)

        if date_from > date_to:
            return error_response("'from' sanasi 'to' dan katta bo'lmasligi kerak")

        group_by = request.query_params.get("group_by", "day")
        trunc = self.TRUNC.get(group_by)
        if trunc is None:
            return error_response("group_by: day, week yoki month")

        qs = Order.objects.filter(
            status=OrderStatus.COMPLETED,
            completed_at__date__gte=date_from,
            completed_at__date__lte=date_to,
        )

        series = (
            qs.annotate(period=trunc("completed_at"))
            .values("period")
            .annotate(revenue=Sum("final_price"), orders=Count("id"))
            .order_by("period")
        )

        totals = qs.aggregate(
            revenue=Sum("final_price"),
            orders=Count("id"),
            avg=Avg("final_price"),
        )

        by_method = list(
            qs.values("payment_method")
            .annotate(revenue=Sum("final_price"), orders=Count("id"))
            .order_by("-revenue")
        )

        return success_response(
            data={
                "from": date_from,
                "to": date_to,
                "group_by": group_by,
                "total_revenue": totals["revenue"] or 0,
                "total_orders": totals["orders"] or 0,
                "average_check": round(totals["avg"] or 0),
                "by_payment_method": by_method,
                "series": [
                    {
                        "period": row["period"],
                        "revenue": row["revenue"] or 0,
                        "orders": row["orders"],
                    }
                    for row in series
                ],
            }
        )


# =====================================================================
# 2. FOYDALANUVCHILAR
# =====================================================================
class AdminUserListView(AdminListView):
    """GET /api/admin/users/?role=&is_active=&search=&ordering="""

    serializer_class = AdminUserSerializer
    filterset_class = UserFilter
    search_fields = ["phone", "full_name", "email"]
    ordering_fields = ["created_at", "full_name", "last_login"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return User.objects.annotate(orders_count=Count("orders")).select_related(
            "driver"
        )


class AdminUserDetailView(AdminAPIView):
    """GET /api/admin/users/{id}/ — user + oxirgi 10 buyurtma."""

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def get(self, request, pk):
        user = (
            User.objects.annotate(orders_count=Count("orders"))
            .filter(pk=pk)
            .first()
        )
        if user is None:
            return error_response("Foydalanuvchi topilmadi", status=404)

        last_orders = (
            Order.objects.filter(client=user)
            .select_related("client", "driver__user", "tariff")
            .order_by("-created_at")[:10]
        )

        return success_response(
            data={
                "user": AdminUserSerializer(user).data,
                "last_orders": AdminOrderSerializer(last_orders, many=True).data,
            }
        )


class AdminUserBlockView(AdminAPIView):
    """PATCH /api/admin/users/{id}/block/  body: {"is_active": false}"""

    @extend_schema(request=BlockSerializer, responses=AdminUserSerializer, tags=["admin"])
    def patch(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if user is None:
            return error_response("Foydalanuvchi topilmadi", status=404)
        if user.id == request.user.id:
            return error_response("O'zingizni bloklay olmaysiz", status=400)
        if user.is_superuser:
            return error_response("Superuser'ni bloklab bo'lmaydi", status=403)

        serializer = BlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.is_active = serializer.validated_data["is_active"]
        user.save(update_fields=["is_active", "updated_at"])

        return success_response(
            data=AdminUserSerializer(user).data,
            message="Foydalanuvchi faollashtirildi" if user.is_active else "Foydalanuvchi bloklandi",
        )


# =====================================================================
# 3. HAYDOVCHILAR
# =====================================================================
class AdminDriverListView(AdminListView):
    """GET /api/admin/drivers/?is_active=&is_online=&search="""

    serializer_class = AdminDriverSerializer
    filterset_class = DriverFilter
    search_fields = [
        "user__phone", "user__full_name", "car_number", "car_model",
    ]
    ordering_fields = ["created_at", "rating", "total_trips"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Driver.objects.select_related("user").annotate(
            orders_count=Count("orders")
        )


class AdminDriverDetailView(AdminAPIView):
    """GET / PATCH /api/admin/drivers/{id}/"""

    def get_driver(self, pk):
        return (
            Driver.objects.select_related("user")
            .annotate(orders_count=Count("orders"))
            .filter(pk=pk)
            .first()
        )

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def get(self, request, pk):
        driver = self.get_driver(pk)
        if driver is None:
            return error_response("Haydovchi topilmadi", status=404)

        last_orders = (
            Order.objects.filter(driver=driver)
            .select_related("client", "driver__user", "tariff")
            .order_by("-created_at")[:10]
        )
        earnings = Order.objects.filter(
            driver=driver, status=OrderStatus.COMPLETED
        ).aggregate(total=Sum("final_price"), trips=Count("id"))

        return success_response(
            data={
                "driver": AdminDriverSerializer(driver).data,
                "earnings": {
                    "total": earnings["total"] or 0,
                    "completed_trips": earnings["trips"],
                },
                "last_orders": AdminOrderSerializer(last_orders, many=True).data,
            }
        )

    @extend_schema(request=AdminDriverUpdateSerializer, responses=AdminDriverSerializer, tags=["admin"])
    def patch(self, request, pk):
        driver = Driver.objects.filter(pk=pk).first()
        if driver is None:
            return error_response("Haydovchi topilmadi", status=404)

        serializer = AdminDriverUpdateSerializer(
            driver, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            data=AdminDriverSerializer(self.get_driver(pk)).data,
            message="Haydovchi ma'lumotlari yangilandi",
        )


class AdminDriverApproveView(AdminAPIView):
    """PATCH /api/admin/drivers/{id}/approve/  body: {"is_active": true}

    Hujjatlari tekshirilgach haydovchini tasdiqlaydi. is_active=False
    yuborilsa tasdiq bekor qilinadi (haydovchi offline'ga o'tkaziladi).
    """

    @extend_schema(request=BlockSerializer, responses=AdminDriverSerializer, tags=["admin"])
    def patch(self, request, pk):
        driver = Driver.objects.select_related("user").filter(pk=pk).first()
        if driver is None:
            return error_response("Haydovchi topilmadi", status=404)

        # body bo'sh bo'lsa — tasdiqlash deb qabul qilamiz
        is_active = request.data.get("is_active", True)
        serializer = BlockSerializer(data={"is_active": is_active})
        serializer.is_valid(raise_exception=True)
        approved = serializer.validated_data["is_active"]

        if approved and not driver.car_number:
            return error_response(
                "Mashina raqami kiritilmagan — tasdiqlab bo'lmaydi", status=400
            )

        # Hujjatsiz tasdiqlash mantiqsiz: admin nimani ko'rib tasdiqlaydi?
        if approved and not driver.has_documents:
            yetishmayotgan = ", ".join(driver.missing_documents)
            return error_response(
                f"Hujjatlar yetishmayapti: {yetishmayotgan}", status=400
            )

        driver.is_active = approved
        fields = ["is_active", "updated_at"]
        if not approved:
            driver.is_online = False
            fields.append("is_online")
        driver.save(update_fields=fields)

        if approved and not driver.user.is_verified:
            driver.user.is_verified = True
            driver.user.save(update_fields=["is_verified", "updated_at"])

        return success_response(
            data=AdminDriverSerializer(driver).data,
            message="Haydovchi tasdiqlandi" if approved else "Tasdiq bekor qilindi",
        )


class AdminDriverBlockView(AdminAPIView):
    """PATCH /api/admin/drivers/{id}/block/  body: {"is_active": false}

    Approve'dan farqi: bu user hisobini bloklaydi (login qila olmaydi).
    """

    @extend_schema(request=BlockSerializer, responses=AdminDriverSerializer, tags=["admin"])
    def patch(self, request, pk):
        driver = Driver.objects.select_related("user").filter(pk=pk).first()
        if driver is None:
            return error_response("Haydovchi topilmadi", status=404)

        serializer = BlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        active = serializer.validated_data["is_active"]

        driver.user.is_active = active
        driver.user.save(update_fields=["is_active", "updated_at"])

        if not active:
            driver.is_online = False
            driver.save(update_fields=["is_online", "updated_at"])

        return success_response(
            data=AdminDriverSerializer(driver).data,
            message="Haydovchi blokdan chiqarildi" if active else "Haydovchi bloklandi",
        )


# =====================================================================
# 4. BUYURTMALAR
# =====================================================================
class AdminOrderListView(AdminListView):
    """GET /api/admin/orders/?status=&created_from=&created_to=&search="""

    serializer_class = AdminOrderSerializer
    filterset_class = OrderFilter
    search_fields = [
        "from_address", "to_address",
        "client__phone", "client__full_name",
        "driver__user__phone", "driver__car_number",
    ]
    ordering_fields = ["created_at", "estimated_price", "final_price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Order.objects.select_related(
            "client", "driver__user", "tariff"
        )


class AdminOrderDetailView(AdminAPIView):
    """GET /api/admin/orders/{id}/ — buyurtma + to'lovlar tarixi."""

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def get(self, request, pk):
        order = (
            Order.objects.select_related("client", "driver__user", "tariff")
            .filter(pk=pk)
            .first()
        )
        if order is None:
            return error_response("Buyurtma topilmadi", status=404)

        payments = order.payments.select_related("order__client").order_by("-created_at")

        return success_response(
            data={
                "order": AdminOrderSerializer(order).data,
                "payments": AdminPaymentSerializer(payments, many=True).data,
            }
        )


class AdminOrderCancelView(AdminAPIView):
    """PATCH /api/admin/orders/{id}/cancel/  body: {"reason": "..."}"""

    @extend_schema(request=AdminCancelOrderSerializer, responses=AdminOrderSerializer, tags=["admin"])
    def patch(self, request, pk):
        order = Order.objects.select_related(
            "client", "driver__user", "tariff"
        ).filter(pk=pk).first()
        if order is None:
            return error_response("Buyurtma topilmadi", status=404)

        if order.status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            return error_response(
                f"'{order.get_status_display()}' holatidagi buyurtmani bekor qilib bo'lmaydi",
                status=400,
            )

        serializer = AdminCancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "")

        order.cancel_reason = reason or "Admin tomonidan bekor qilindi"
        order.save(update_fields=["cancel_reason", "updated_at"])
        order = change_status(order, OrderStatus.CANCELLED)

        Payment.objects.filter(order=order, status=PaymentState.PENDING).update(
            status=PaymentState.CANCELLED
        )

        return success_response(
            data=AdminOrderSerializer(order).data,
            message="Buyurtma bekor qilindi",
        )


class AdminOrderAssignDriverView(AdminAPIView):
    """PATCH /api/admin/orders/{id}/assign/  body: {"driver_id": 5}

    Operator qo'lda haydovchi biriktiradi (pending buyurtma uchun).
    """

    @extend_schema(request=AdminAssignDriverSerializer, responses=AdminOrderSerializer, tags=["admin"])
    def patch(self, request, pk):
        order = Order.objects.select_related(
            "client", "driver__user", "tariff"
        ).filter(pk=pk).first()
        if order is None:
            return error_response("Buyurtma topilmadi", status=404)

        serializer = AdminAssignDriverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        driver = Driver.objects.select_related("user").filter(
            pk=serializer.validated_data["driver_id"]
        ).first()
        if driver is None:
            return error_response("Haydovchi topilmadi", status=404)
        if not driver.is_active:
            return error_response("Haydovchi tasdiqlanmagan", status=400)

        order = change_status(order, OrderStatus.ACCEPTED, driver=driver)
        return success_response(
            data=AdminOrderSerializer(order).data,
            message="Haydovchi biriktirildi",
        )


# =====================================================================
# 5. TARIFLAR (CRUD)
# =====================================================================
class AdminTariffListCreateView(AdminAPIView):
    """GET / POST /api/admin/tariffs/"""

    @extend_schema(responses=AdminTariffSerializer(many=True), tags=["admin"])
    def get(self, request):
        tariffs = Tariff.objects.annotate(orders_count=Count("orders"))
        return success_response(
            data=AdminTariffSerializer(tariffs, many=True).data
        )

    @extend_schema(request=AdminTariffSerializer, responses=AdminTariffSerializer, tags=["admin"])
    def post(self, request):
        serializer = AdminTariffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data, message="Tarif qo'shildi", status=201
        )


class AdminTariffDetailView(AdminAPIView):
    """GET / PATCH / DELETE /api/admin/tariffs/{id}/"""

    def get_object(self, pk):
        return Tariff.objects.annotate(orders_count=Count("orders")).filter(
            pk=pk
        ).first()

    @extend_schema(responses=AdminTariffSerializer, tags=["admin"])
    def get(self, request, pk):
        tariff = self.get_object(pk)
        if tariff is None:
            return error_response("Tarif topilmadi", status=404)
        return success_response(data=AdminTariffSerializer(tariff).data)

    @extend_schema(request=AdminTariffSerializer, responses=AdminTariffSerializer, tags=["admin"])
    def patch(self, request, pk):
        tariff = self.get_object(pk)
        if tariff is None:
            return error_response("Tarif topilmadi", status=404)
        serializer = AdminTariffSerializer(tariff, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Tarif yangilandi")

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def delete(self, request, pk):
        tariff = self.get_object(pk)
        if tariff is None:
            return error_response("Tarif topilmadi", status=404)

        # Order.tariff = PROTECT -> ishlatilgan tarifni o'chirib bo'lmaydi
        if tariff.orders.exists():
            tariff.is_active = False
            tariff.save(update_fields=["is_active"])
            return success_response(
                data=AdminTariffSerializer(self.get_object(pk)).data,
                message="Tarifda buyurtmalar bor — o'chirish o'rniga o'chirib qo'yildi",
            )

        tariff.delete()
        return success_response(message="Tarif o'chirildi")


# =====================================================================
# 6. TO'LOVLAR
# =====================================================================
class AdminPaymentListView(AdminListView):
    """GET /api/admin/payments/?status=&method=&created_from="""

    serializer_class = AdminPaymentSerializer
    filterset_class = PaymentFilter
    search_fields = [
        "transaction_id", "order__client__phone", "order__client__full_name",
    ]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Payment.objects.select_related("order__client")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        totals = self.filter_queryset(self.get_queryset()).aggregate(
            paid=Sum("amount", filter=Q(status=PaymentState.PAID)),
            all_amount=Sum("amount"),
        )
        response.data["data"]["summary"] = {
            "paid_amount": totals["paid"] or 0,
            "total_amount": totals["all_amount"] or 0,
        }
        return response


# =====================================================================
# 7. SO'ROVLAR (og'ir texnika + to'y)
# =====================================================================
class AdminHeavyRequestListView(AdminListView):
    """GET /api/admin/requests/heavy/?status=&category=&search="""

    serializer_class = AdminHeavyRequestSerializer
    filterset_class = HeavyRequestFilter
    search_fields = ["contact_name", "contact_phone", "address"]
    ordering_fields = ["created_at", "start_date"]
    ordering = ["-created_at"]
    queryset = HeavyEquipmentRequest.objects.all()


class AdminWeddingRequestListView(AdminListView):
    """GET /api/admin/requests/wedding/?status=&search="""

    serializer_class = AdminWeddingRequestSerializer
    filterset_class = WeddingRequestFilter
    search_fields = ["contact_name", "contact_phone", "address", "car_brand"]
    ordering_fields = ["created_at", "date"]
    ordering = ["-created_at"]
    queryset = WeddingRequest.objects.all()


class BaseRequestDetailView(AdminAPIView):
    """Og'ir texnika / to'y so'rovi uchun umumiy detail + status view."""

    model = None
    serializer_class = None

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def get(self, request, pk):
        obj = self.model.objects.filter(pk=pk).first()
        if obj is None:
            return error_response("So'rov topilmadi", status=404)
        return success_response(data=self.serializer_class(obj).data)

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, tags=["admin"])
    def patch(self, request, pk):
        obj = self.model.objects.filter(pk=pk).first()
        if obj is None:
            return error_response("So'rov topilmadi", status=404)
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="So'rov yangilandi")

    @extend_schema(responses=OpenApiTypes.OBJECT, tags=["admin"])
    def delete(self, request, pk):
        obj = self.model.objects.filter(pk=pk).first()
        if obj is None:
            return error_response("So'rov topilmadi", status=404)
        obj.delete()
        return success_response(message="So'rov o'chirildi")


class AdminHeavyRequestDetailView(BaseRequestDetailView):
    model = HeavyEquipmentRequest
    serializer_class = AdminHeavyRequestSerializer


class AdminWeddingRequestDetailView(BaseRequestDetailView):
    model = WeddingRequest
    serializer_class = AdminWeddingRequestSerializer


class BaseRequestStatusView(AdminAPIView):
    """PATCH .../{id}/status/  body: {"status": "contacted", "notes": "..."}"""

    model = None
    serializer_class = None

    @extend_schema(request=RequestStatusSerializer, responses=OpenApiTypes.OBJECT, tags=["admin"])
    def patch(self, request, pk):
        obj = self.model.objects.filter(pk=pk).first()
        if obj is None:
            return error_response("So'rov topilmadi", status=404)

        serializer = RequestStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj.status = serializer.validated_data["status"]
        fields = ["status", "updated_at"]

        notes = serializer.validated_data.get("notes")
        if notes:
            stamp = timezone.localtime().strftime("%d.%m.%Y %H:%M")
            prefix = f"{obj.notes}\n" if obj.notes else ""
            obj.notes = f"{prefix}[{stamp}] {notes}"
            fields.append("notes")

        obj.save(update_fields=fields)
        return success_response(
            data=self.serializer_class(obj).data, message="Status yangilandi"
        )


class AdminHeavyRequestStatusView(BaseRequestStatusView):
    model = HeavyEquipmentRequest
    serializer_class = AdminHeavyRequestSerializer


class AdminWeddingRequestStatusView(BaseRequestStatusView):
    model = WeddingRequest
    serializer_class = AdminWeddingRequestSerializer
