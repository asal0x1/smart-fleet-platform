from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsDriver
from apps.common.responses import error_response, success_response
from apps.drivers.models import Driver

from .models import Order, OrderStatus, Review, ReviewKind, Tariff
from .serializers import (
    ChangeStatusSerializer,
    CreateOrderSerializer,
    CreateReviewSerializer,
    EstimateSerializer,
    OrderSerializer,
    ReviewSerializer,
    TariffSerializer,
)
from .services import (
    change_status,
    create_order,
    estimate_order,
    recalculate_driver_rating,
)


def is_admin(user):
    return user.role == "admin" or user.is_staff


def get_driver_profile(user):
    """Faqat mavjud profilni qaytaradi — YARATMAYDI.

    Ilgari bu yerda get_or_create ishlatilardi va mijoz `accepted` yuborsa
    unga Driver obyekti yaratilib, mijoz haydovchiga aylanib qolardi.
    """
    if user.role != "driver":
        return None
    return Driver.objects.filter(user=user).first()


class TariffListView(APIView):
    """Faol tariflar.

    Ilgari ListAPIView edi va {"success": ...} konvertisiz massiv
    qaytarardi — loyihadagi boshqa hamma endpointdan farq qilardi.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tariffs = Tariff.objects.filter(is_active=True)
        return success_response(data=TariffSerializer(tariffs, many=True).data)


class EstimateView(APIView):
    """Order yaratmasdan narxni oldindan hisoblash."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EstimateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        tariff = Tariff.objects.filter(id=d["tariff_id"], is_active=True).first()
        if tariff is None:
            return error_response("Tarif topilmadi", status=404)
        result = estimate_order(
            tariff, d["from_lat"], d["from_lng"], d["to_lat"], d["to_lng"]
        )
        return success_response(data=result)


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Foydalanuvchining buyurtmalari (mijoz yoki haydovchi)."""
        user = request.user
        status_filter = request.query_params.get("status")

        if is_admin(user):
            qs = Order.objects.all()
        elif user.role == "driver":
            driver = get_driver_profile(user)
            qs = Order.objects.filter(driver=driver) if driver else Order.objects.none()
        else:
            qs = Order.objects.filter(client=user)

        if status_filter and status_filter != "all":
            qs = qs.filter(status=status_filter)

        # To'liq sahifalash o'rniga oddiy limit — ro'yxat vaqt o'tishi bilan
        # cheksiz o'sib, javobni sekinlashtirmasligi uchun. Model bo'yicha
        # standart tartib -created_at, shuning uchun eng so'nggilari qoladi.
        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), 200)
        except (TypeError, ValueError):
            limit = 50

        qs = qs.select_related("client", "driver__user", "tariff")[:limit]
        data = OrderSerializer(qs, many=True).data
        return success_response(data=data)

    def post(self, request):
        """Yangi buyurtma — faqat mijoz."""
        if request.user.role == "driver":
            return error_response(
                "Haydovchi buyurtma bera olmaydi", status=403
            )

        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = create_order(request.user, serializer.validated_data)
        return success_response(
            data=OrderSerializer(order).data,
            message="Buyurtma yaratildi",
            status=201,
        )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        user = request.user
        order = Order.objects.select_related(
            "client", "driver__user", "tariff"
        ).filter(pk=pk).first()
        if order is None:
            return None, error_response("Buyurtma topilmadi", status=404)
        # Faqat egasi/haydovchi/admin ko'ra oladi
        if is_admin(user):
            return order, None
        if order.client_id == user.id:
            return order, None
        if order.driver and order.driver.user_id == user.id:
            return order, None
        return None, error_response("Ruxsat yo'q", status=403)

    def get(self, request, pk):
        order, err = self.get_object(request, pk)
        if err:
            return err
        return success_response(data=OrderSerializer(order).data)


class ChangeStatusView(APIView):
    """Buyurtma statusini o'zgartirish.

    Kim nima qila oladi:
      accepted                     -> faqat tasdiqlangan haydovchi (buyurtma bo'sh bo'lsa)
      driver_arrived/ongoing/completed -> faqat shu buyurtmaga biriktirilgan haydovchi
      cancelled                    -> buyurtma egasi, biriktirilgan haydovchi yoki admin
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        user = request.user

        # accepted holatida ikki haydovchi bir vaqtda urinishi mumkin —
        # qatorni qulflab olamiz
        with transaction.atomic():
            # of=("self",) muhim: driver nullable bo'lgani uchun select_related
            # LEFT OUTER JOIN yasaydi, PostgreSQL esa uni qulflashga ruxsat
            # bermaydi ("FOR UPDATE cannot be applied to the nullable side of
            # an outer join"). of=("self",) faqat orders qatorini qulflaydi.
            order = (
                Order.objects.select_for_update(of=("self",))
                .select_related("client", "driver__user", "tariff")
                .filter(pk=pk)
                .first()
            )
            if order is None:
                return error_response("Buyurtma topilmadi", status=404)

            driver = None

            if new_status == OrderStatus.ACCEPTED:
                if is_admin(user):
                    return error_response(
                        "Admin buyurtmani /api/admin/orders/{id}/assign/ "
                        "orqali biriktiradi",
                        status=400,
                    )
                driver = get_driver_profile(user)
                if driver is None:
                    return error_response(
                        "Buyurtmani faqat haydovchi qabul qila oladi", status=403
                    )
                if not driver.is_active:
                    return error_response(
                        "Profilingiz hali tasdiqlanmagan", status=403
                    )
                if order.driver_id is not None:
                    return error_response(
                        "Buyurtma allaqachon boshqa haydovchiga biriktirilgan",
                        status=409,
                    )

            elif new_status in (
                OrderStatus.DRIVER_ARRIVED,
                OrderStatus.ONGOING,
                OrderStatus.COMPLETED,
            ):
                if not is_admin(user) and not (
                    order.driver and order.driver.user_id == user.id
                ):
                    return error_response(
                        "Bu buyurtma sizga biriktirilmagan", status=403
                    )

            elif new_status == OrderStatus.CANCELLED:
                allowed = (
                    is_admin(user)
                    or order.client_id == user.id
                    or (order.driver and order.driver.user_id == user.id)
                )
                if not allowed:
                    return error_response("Ruxsat yo'q", status=403)

            order = change_status(
                order, new_status, driver=driver,
                actual_distance_km=serializer.validated_data.get(
                    "actual_distance_km"
                ),
            )

        return success_response(
            data=OrderSerializer(order).data,
            message="Status yangilandi",
        )


class AvailableOrdersView(APIView):
    """Haydovchi uchun ochiq (pending) buyurtmalar.

    Haydovchi joylashuviga yaqinlari birinchi chiqadi.
    """

    permission_classes = [IsDriver]

    #: Haydovchi ko'radigan maksimal masofa (metr)
    DEFAULT_RADIUS_M = 15_000
    MAX_RADIUS_M = 50_000

    def get(self, request):
        return success_response(
            data=OrderSerializer(self.get_queryset(), many=True).data
        )

    def get_queryset(self):
        driver = get_driver_profile(self.request.user)
        # Tasdiqlanmagan haydovchi buyurtmalarni ko'rmasligi kerak
        if driver is None or not driver.is_active:
            return Order.objects.none()

        qs = (
            Order.objects.filter(status=OrderStatus.PENDING, driver__isnull=True)
            .select_related("client", "tariff")
        )

        # Toshkentdagi haydovchi Samarqand buyurtmasini ko'rmasligi kerak.
        # Joylashuv hali yuborilmagan bo'lsa filtrlamaymiz — aks holda
        # yangi haydovchi hech nima ko'rmaydi.
        if driver.location is not None:
            radius = self._radius()
            qs = (
                qs.filter(from_location__dwithin=(driver.location, D(m=radius)))
                .annotate(distance=Distance("from_location", driver.location))
                .order_by("distance")
            )
            return qs

        return qs.order_by("-created_at")

    def _radius(self):
        try:
            radius = int(self.request.query_params.get("radius", self.DEFAULT_RADIUS_M))
        except (TypeError, ValueError):
            return self.DEFAULT_RADIUS_M
        return max(500, min(radius, self.MAX_RADIUS_M))


class OrderReviewView(APIView):
    """POST /api/orders/{id}/review/  {"rating": 5, "comment": "..."}

    Faqat YAKUNLANGAN safar uchun. Mijoz haydovchini, haydovchi mijozni
    baholaydi — har biri bir martadan.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = Order.objects.filter(pk=pk).first()
        if order is None:
            return error_response("Buyurtma topilmadi", status=404)
        reviews = order.reviews.select_related("author")
        return success_response(data=ReviewSerializer(reviews, many=True).data)

    def post(self, request, pk):
        order = (
            Order.objects.select_related("client", "driver__user")
            .filter(pk=pk)
            .first()
        )
        if order is None:
            return error_response("Buyurtma topilmadi", status=404)

        if order.status != OrderStatus.COMPLETED:
            return error_response(
                "Baho faqat yakunlangan safar uchun beriladi", status=400
            )

        user = request.user
        if order.client_id == user.id:
            kind = ReviewKind.CLIENT_TO_DRIVER
        elif order.driver and order.driver.user_id == user.id:
            kind = ReviewKind.DRIVER_TO_CLIENT
        else:
            return error_response("Bu safar sizga tegishli emas", status=403)

        if Review.objects.filter(order=order, kind=kind).exists():
            return error_response("Siz allaqachon baho bergansiz", status=409)

        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = Review.objects.create(
            order=order,
            author=user,
            kind=kind,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )

        # Mijoz baho bergan bo'lsa haydovchi reytingi yangilanadi
        if kind == ReviewKind.CLIENT_TO_DRIVER and order.driver:
            recalculate_driver_rating(order.driver)

        return success_response(
            data=ReviewSerializer(review).data,
            message="Baho qabul qilindi",
            status=201,
        )
