from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import success_response
from apps.common.throttling import RequestFormThrottle
from services.email import email_service

from .models import (
    BusRequest,
    GiftMemorialRequest,
    HeavyEquipmentRequest,
    PersonalDriverRequest,
    WeddingRequest,
)
from .serializers import (
    BusRequestSerializer,
    GiftMemorialRequestSerializer,
    HeavyEquipmentRequestSerializer,
    PersonalDriverRequestSerializer,
    WeddingRequestSerializer,
)
from .services import (
    bus_price,
    gift_memorial_price,
    heavy_equipment_price,
    personal_driver_price,
    wedding_price,
)


class HeavyEquipmentRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RequestFormThrottle]

    def post(self, request):
        serializer = HeavyEquipmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        creator = request.user if request.user.is_authenticated else None
        req = serializer.save(created_by=creator)

        req.estimated_price = heavy_equipment_price(
            req.category, req.items, req.duration_days
        )
        req.save(update_fields=["estimated_price"])

        email_service.send_heavy_equipment_request(req)

        return success_response(
            data={
                "request_id": req.id,
                "status": req.status,
                "estimated_price": req.estimated_price,
                "message": "So'rovingiz qabul qilindi. Operatorimiz tez orada bog'lanadi.",
            },
            status=201,
        )


class MyHeavyEquipmentRequestsView(APIView):
    """GET /api/heavy-equipment/requests/mine/ — kirgan foydalanuvchi yuborgan so'rovlar."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = HeavyEquipmentRequest.objects.filter(created_by=request.user)
        return success_response(data=HeavyEquipmentRequestSerializer(qs, many=True).data)


class WeddingRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RequestFormThrottle]

    def post(self, request):
        serializer = WeddingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        creator = request.user if request.user.is_authenticated else None
        req = serializer.save(created_by=creator)

        # Taxminiy narx hisoblash
        req.estimated_price = wedding_price(req.car_count, req.duration_hours)
        req.save(update_fields=["estimated_price"])

        email_service.send_wedding_request(req)

        return success_response(
            data={
                "request_id": req.id,
                "status": req.status,
                "estimated_price": req.estimated_price,
                "message": "So'rovingiz qabul qilindi. Operator tez orada bog'lanadi.",
            },
            status=201,
        )


class MyWeddingRequestsView(APIView):
    """GET /api/wedding/requests/mine/ — kirgan foydalanuvchi yuborgan so'rovlar."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = WeddingRequest.objects.filter(created_by=request.user)
        return success_response(data=WeddingRequestSerializer(qs, many=True).data)


class PersonalDriverRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RequestFormThrottle]

    def post(self, request):
        serializer = PersonalDriverRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        creator = request.user if request.user.is_authenticated else None
        req = serializer.save(created_by=creator)

        req.estimated_price = personal_driver_price(req.contract_duration)
        req.save(update_fields=["estimated_price"])

        email_service.send_personal_driver_request(req)

        return success_response(
            data={
                "request_id": req.id,
                "status": req.status,
                "estimated_price": req.estimated_price,
                "message": "So'rovingiz qabul qilindi. Operator tez orada bog'lanadi.",
            },
            status=201,
        )


class MyPersonalDriverRequestsView(APIView):
    """GET /api/personal-driver/requests/mine/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = PersonalDriverRequest.objects.filter(created_by=request.user)
        return success_response(data=PersonalDriverRequestSerializer(qs, many=True).data)


class BusRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RequestFormThrottle]

    def post(self, request):
        serializer = BusRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        creator = request.user if request.user.is_authenticated else None
        req = serializer.save(created_by=creator)

        req.estimated_price = bus_price(req.bus_count, req.duration_hours)
        req.save(update_fields=["estimated_price"])

        email_service.send_bus_request(req)

        return success_response(
            data={
                "request_id": req.id,
                "status": req.status,
                "estimated_price": req.estimated_price,
                "message": "So'rovingiz qabul qilindi. Operator tez orada bog'lanadi.",
            },
            status=201,
        )


class MyBusRequestsView(APIView):
    """GET /api/bus/requests/mine/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = BusRequest.objects.filter(created_by=request.user)
        return success_response(data=BusRequestSerializer(qs, many=True).data)


class GiftMemorialRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RequestFormThrottle]

    def post(self, request):
        serializer = GiftMemorialRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        creator = request.user if request.user.is_authenticated else None
        req = serializer.save(created_by=creator)

        req.estimated_price = gift_memorial_price(req.kind)
        req.save(update_fields=["estimated_price"])

        email_service.send_gift_memorial_request(req)

        return success_response(
            data={
                "request_id": req.id,
                "status": req.status,
                "estimated_price": req.estimated_price,
                "message": "So'rovingiz qabul qilindi. Operator tez orada bog'lanadi.",
            },
            status=201,
        )


class MyGiftMemorialRequestsView(APIView):
    """GET /api/gift-memorial/requests/mine/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = GiftMemorialRequest.objects.filter(created_by=request.user)
        return success_response(data=GiftMemorialRequestSerializer(qs, many=True).data)
