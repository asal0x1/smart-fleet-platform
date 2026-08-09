from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsDriver
from apps.common.responses import error_response, success_response
from apps.notifications.services import broadcast_driver_location
from apps.orders.models import Order, OrderStatus

from .models import Driver
from .serializers import (
    DriverDocumentsSerializer,
    DriverProfileSerializer,
    LocationUpdateSerializer,
    NearbyDriverSerializer,
    NearbyQuerySerializer,
    OnlineStatusSerializer,
)


def get_or_create_driver(user):
    """Haydovchi profilini qaytaradi, kerak bo'lsa yaratadi.

    XAVFSIZLIK: faqat role="driver" bo'lgan foydalanuvchi uchun.
    Ilgari bu tekshiruv yo'q edi va mijoz buyurtmaga `accepted` yuborsa
    unga Driver obyekti yaratilib, mijoz haydovchiga aylanib qolardi.
    """
    if user.role != "driver":
        return None
    driver, _ = Driver.objects.get_or_create(user=user)
    return driver


class DriverProfileView(APIView):
    permission_classes = [IsDriver]

    def get(self, request):
        driver = get_or_create_driver(request.user)
        return success_response(
            data=DriverProfileSerializer(driver, context={"request": request}).data
        )

    def patch(self, request):
        driver = get_or_create_driver(request.user)
        serializer = DriverProfileSerializer(
            driver, data=request.data, partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data, message="Profil yangilandi"
        )


class DriverDocumentsView(APIView):
    """Hujjat rasmlarini yuklash — multipart/form-data.

    POST /api/drivers/documents/
      license_photo, tech_passport_photo, passport_photo, car_photo
    """

    permission_classes = [IsDriver]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        driver = get_or_create_driver(request.user)
        return success_response(
            data=DriverDocumentsSerializer(
                driver, context={"request": request}
            ).data
        )

    def post(self, request):
        driver = get_or_create_driver(request.user)
        serializer = DriverDocumentsSerializer(
            driver, data=request.data, partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        driver = serializer.save()

        xabar = (
            "Hujjatlar to'liq — admin tasdig'ini kuting"
            if driver.has_documents
            else "Hujjat yuklandi, lekin ba'zilari yetishmayapti"
        )
        return success_response(data=serializer.data, message=xabar)


class UpdateLocationView(APIView):
    permission_classes = [IsDriver]

    def post(self, request):
        driver = get_or_create_driver(request.user)
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(driver)

        # Faol safar bo'lsa mijoz haydovchini xaritada real vaqtda ko'radi
        faol = (
            Order.objects.filter(
                driver=driver,
                status__in=[
                    OrderStatus.ACCEPTED,
                    OrderStatus.DRIVER_ARRIVED,
                    OrderStatus.ONGOING,
                ],
            )
            .only("id")
            .first()
        )
        if faol is not None:
            broadcast_driver_location(
                faol,
                serializer.validated_data["lat"],
                serializer.validated_data["lng"],
            )

        return success_response(message="Joylashuv yangilandi")


class OnlineToggleView(APIView):
    permission_classes = [IsDriver]

    def post(self, request):
        driver = get_or_create_driver(request.user)
        serializer = OnlineStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        going_online = serializer.validated_data["is_online"]
        if going_online and not driver.is_active:
            return error_response(
                "Profilingiz hali tasdiqlanmagan — onlayn bo'la olmaysiz",
                status=403,
            )

        driver.is_online = going_online
        driver.save(update_fields=["is_online", "updated_at"])
        return success_response(
            data={"is_online": driver.is_online},
            message="Holat yangilandi",
        )


class NearbyDriversView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = NearbyQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        point = Point(d["lng"], d["lat"], srid=4326)

        drivers = (
            Driver.objects.filter(
                is_online=True,
                is_active=True,
                location__isnull=False,
                location__dwithin=(point, D(m=d["radius"])),
            )
            .select_related("user")
            .annotate(distance=Distance("location", point))
            .order_by("distance")[: d["limit"]]
        )

        data = NearbyDriverSerializer(drivers, many=True).data
        return success_response(data={"drivers": data})
