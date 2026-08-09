from django.db import transaction
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.responses import error_response, success_response
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user
from apps.orders.models import Order, OrderStatus
from services.payment import (
    CLICK_ALREADY_PAID,
    CLICK_INVALID_AMOUNT,
    CLICK_ORDER_NOT_FOUND,
    CLICK_SIGN_ERROR,
    CLICK_SUCCESS,
    CLICK_TRANSACTION_CANCELLED,
    CLICK_TRANSACTION_NOT_FOUND,
    click_service,
)

from .models import Payment, PaymentState


def client_ip(request):
    """Nginx orqasida bo'lsa X-Forwarded-For dagi birinchi IP haqiqiy manba."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def click_error(code, note):
    return Response({"error": code, "error_note": note})


class CreatePaymentView(APIView):
    """Order uchun to'lov boshlash (Click havolasi qaytaradi)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        method = request.data.get("method", "click")

        if method not in ("click", "payme", "cash"):
            return error_response("Noto'g'ri to'lov usuli", status=400)

        order = Order.objects.filter(id=order_id, client=request.user).first()
        if order is None:
            return error_response("Buyurtma topilmadi", status=404)

        if order.status == OrderStatus.CANCELLED:
            return error_response(
                "Bekor qilingan buyurtma uchun to'lov qilib bo'lmaydi", status=400
            )
        if order.payment_status == "paid":
            return error_response("Buyurtma allaqachon to'langan", status=400)

        amount = order.final_price or order.estimated_price
        if not amount:
            return error_response("Buyurtma summasi aniqlanmagan", status=400)

        # Ochiq qolgan eski to'lovni qayta ishlatamiz — har bosishda
        # yangi Payment yaratilib ketmasin
        payment = (
            Payment.objects.filter(
                order=order, method=method, status=PaymentState.PENDING
            )
            .order_by("-created_at")
            .first()
        )
        if payment is None or payment.amount != amount:
            payment = Payment.objects.create(
                order=order, amount=amount, method=method,
                status=PaymentState.PENDING,
            )

        if method == "click":
            url = click_service.create_payment_url(order.id, amount)
            return success_response(
                data={
                    "payment_id": payment.id,
                    "click_url": url,
                    "amount": amount,
                    "status": "pending",
                }
            )

        return success_response(
            data={"payment_id": payment.id, "amount": amount, "status": "pending"}
        )


class ClickPrepareView(APIView):
    """Click Prepare bosqichi (action=0)."""
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        if not click_service.is_allowed_ip(client_ip(request)):
            return click_error(CLICK_SIGN_ERROR, "Ruxsat etilmagan IP")

        if not click_service.check_prepare_signature(data):
            return click_error(CLICK_SIGN_ERROR, "Imzo xato")

        order_id = data.get("merchant_trans_id")
        order = Order.objects.filter(id=order_id).first()
        if order is None:
            return click_error(CLICK_ORDER_NOT_FOUND, "Buyurtma yo'q")

        if order.status == OrderStatus.CANCELLED:
            return click_error(CLICK_TRANSACTION_CANCELLED, "Buyurtma bekor qilingan")

        payment = (
            Payment.objects.filter(order=order, status=PaymentState.PENDING)
            .order_by("-created_at")
            .first()
        )
        if payment is None:
            return click_error(CLICK_TRANSACTION_NOT_FOUND, "To'lov topilmadi")

        # ⚠️ Summani tekshirish — busiz arzon narxda "to'lash" mumkin
        if not click_service.check_amount(data.get("amount"), payment.amount):
            return click_error(CLICK_INVALID_AMOUNT, "Summa mos kelmadi")

        if payment.status == PaymentState.PAID:
            return click_error(CLICK_ALREADY_PAID, "Allaqachon to'langan")

        return Response({
            "click_trans_id": data.get("click_trans_id"),
            "merchant_trans_id": order_id,
            "merchant_prepare_id": payment.id,
            "error": CLICK_SUCCESS,
            "error_note": "Success",
        })


class ClickCompleteView(APIView):
    """Click Complete bosqichi (action=1)."""
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        if not click_service.is_allowed_ip(client_ip(request)):
            return click_error(CLICK_SIGN_ERROR, "Ruxsat etilmagan IP")

        if not click_service.check_complete_signature(data):
            return click_error(CLICK_SIGN_ERROR, "Imzo xato")

        order_id = data.get("merchant_trans_id")
        order = Order.objects.filter(id=order_id).first()
        if order is None:
            return click_error(CLICK_ORDER_NOT_FOUND, "Buyurtma yo'q")

        # ⚠️ merchant_prepare_id — prepare bosqichida BIZ bergan Payment.id.
        # Tekshirilmasa prepare'siz to'g'ridan-to'g'ri complete yuborib
        # to'lovni "o'tkazib" yuborish mumkin.
        prepare_id = data.get("merchant_prepare_id")
        payment = Payment.objects.filter(id=prepare_id, order=order).first()
        if payment is None:
            return click_error(
                CLICK_TRANSACTION_NOT_FOUND, "merchant_prepare_id topilmadi"
            )

        # error < 0 bo'lsa Click to'lovni bekor qilgan
        try:
            click_error_code = int(data.get("error", 0))
        except (TypeError, ValueError):
            click_error_code = 0

        if click_error_code < 0:
            if payment.status != PaymentState.PAID:
                payment.status = PaymentState.CANCELLED
                payment.save(update_fields=["status", "updated_at"])
            return Response({
                "click_trans_id": data.get("click_trans_id"),
                "merchant_trans_id": order_id,
                "error": CLICK_SUCCESS,
                "error_note": "Cancelled",
            })

        # ⚠️ Summa tekshiruvi complete bosqichida ham takrorlanadi
        if not click_service.check_amount(data.get("amount"), payment.amount):
            return click_error(CLICK_INVALID_AMOUNT, "Summa mos kelmadi")

        # Idempotentlik: Click bir xil webhook'ni qayta yuborishi mumkin
        if payment.status == PaymentState.PAID:
            return click_error(CLICK_ALREADY_PAID, "Allaqachon to'langan")

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(pk=payment.pk)
            if payment.status == PaymentState.PAID:
                return click_error(CLICK_ALREADY_PAID, "Allaqachon to'langan")

            payment.status = PaymentState.PAID
            payment.transaction_id = str(data.get("click_trans_id", ""))
            payment.save(update_fields=["status", "transaction_id", "updated_at"])

            order.payment_status = "paid"
            order.save(update_fields=["payment_status", "updated_at"])

        notify_user(
            order.client,
            NotificationType.PAYMENT_PAID,
            "To'lov qabul qilindi",
            f"#{order.id} buyurtma uchun to'lov o'tdi",
            {"order_id": order.id, "payment_id": payment.id},
        )

        return Response({
            "click_trans_id": data.get("click_trans_id"),
            "merchant_trans_id": order_id,
            "merchant_confirm_id": payment.id,
            "error": CLICK_SUCCESS,
            "error_note": "Success",
        })


class ConfirmCashPaymentView(APIView):
    """PATCH /api/payments/{id}/confirm-cash/

    Naqd pulni haydovchi qo'lida qabul qiladi va shu yerda tasdiqlaydi.
    Ilgari naqd to'lov hech qachon "paid" bo'lmasdi — buyurtma yakunlansa
    ham to'lov holati abadiy "pending" bo'lib qolardi.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        payment = (
            Payment.objects.select_related("order__driver__user", "order__client")
            .filter(pk=pk)
            .first()
        )
        if payment is None:
            return error_response("To'lov topilmadi", status=404)

        if payment.method != "cash":
            return error_response(
                "Bu endpoint faqat naqd to'lov uchun", status=400
            )

        order = payment.order
        is_admin = request.user.role == "admin" or request.user.is_staff
        is_driver = bool(order.driver and order.driver.user_id == request.user.id)
        if not (is_admin or is_driver):
            return error_response(
                "Naqd to'lovni faqat haydovchi tasdiqlaydi", status=403
            )

        if payment.status == PaymentState.PAID:
            return error_response("Allaqachon to'langan", status=400)
        if order.status != OrderStatus.COMPLETED:
            return error_response(
                "Safar yakunlanmagan — to'lovni tasdiqlab bo'lmaydi", status=400
            )

        with transaction.atomic():
            payment.status = PaymentState.PAID
            payment.save(update_fields=["status", "updated_at"])
            order.payment_status = "paid"
            order.save(update_fields=["payment_status", "updated_at"])

        notify_user(
            order.client,
            NotificationType.PAYMENT_PAID,
            "To'lov qabul qilindi",
            f"#{order.id} buyurtma uchun {payment.amount:,} so'm".replace(",", " "),
            {"order_id": order.id, "payment_id": payment.id},
        )

        return success_response(
            data={"payment_id": payment.id, "status": payment.status},
            message="Naqd to'lov tasdiqlandi",
        )
