from django.conf import settings
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import error_response, success_response
from apps.common.throttling import (
    LoginRateThrottle,
    OTPVerifyThrottle,
    PasswordResetThrottle,
    PhoneRateThrottle,
    RegisterRateThrottle,
)
from services.sms import sms_service

from .models import User
from .otp import OTPCode
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SendOTPSerializer,
    UserSerializer,
    VerifyOTPSerializer,
    tokens_for_user,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = tokens_for_user(user)
        return success_response(
            data={
                "user_id": user.id,
                "phone": user.phone,
                "role": user.role,
                "token": tokens["access_token"],
            },
            message="Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi",
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = tokens_for_user(user)
        return success_response(
            data={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "expires_in": int(
                    settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
                ),
                "user": UserSerializer(user).data,
            }
        )


class LogoutView(APIView):
    """Refresh token'ni bekor qiladi (blacklist).

    Access token qisqa muddatli bo'lgani uchun u o'zi tugaydi;
    muhimi — refresh token bilan yangi token olib bo'lmasligi.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Tizimdan chiqildi")


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PhoneRateThrottle]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        otp = OTPCode.generate(phone)
        result = sms_service.send_otp(phone, otp.code)

        if not result["ok"]:
            return error_response("SMS yuborishda xatolik", status=502)

        return success_response(
            data={
                "message_id": result["message_id"],
                "expires_in": (otp.expires_at - otp.created_at).seconds
                if otp.created_at
                else 120,
            },
            message="OTP kod yuborildi",
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]

        if not OTPCode.verify(phone, otp):
            return error_response("Kod noto'g'ri yoki muddati o'tgan", status=400)

        # Telefon tasdiqlandi — agar user bo'lsa is_verified=True
        user = User.objects.filter(phone=phone).first()
        data = {}
        if user:
            user.is_verified = True
            user.save(update_fields=["is_verified", "updated_at"])
            tokens = tokens_for_user(user)
            data["token"] = tokens["access_token"]

        return success_response(data=data, message="Telefon tasdiqlandi")


class ChangePasswordView(APIView):
    """Kirgan foydalanuvchi o'z parolini o'zgartiradi."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Parol o'zgargach yangi token beramiz (eskisi bilan ishlashda davom etmasin)
        tokens = tokens_for_user(user)
        return success_response(
            data=tokens, message="Parol o'zgartirildi"
        )


class ResetPasswordView(APIView):
    """OTP orqali parolni tiklash: send-otp/ -> reset-password/"""

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        if not OTPCode.verify(phone, serializer.validated_data["otp"]):
            return error_response("Kod noto'g'ri yoki muddati o'tgan", status=400)

        user = User.objects.filter(phone=phone).first()
        if user is None:
            # Mavjud raqamlarni aniqlab olishga yo'l qo'ymaslik uchun
            # xabar OTP xatosidan farq qilmasligi ma'qul
            return error_response("Kod noto'g'ri yoki muddati o'tgan", status=400)
        if not user.is_active:
            return error_response("Hisob bloklangan", status=403)

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])

        return success_response(
            data=tokens_for_user(user), message="Parol tiklandi"
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    # Avatar yuklash uchun multipart ham qabul qilinadi
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        return success_response(
            data=UserSerializer(request.user, context={"request": request}).data
        )

    def patch(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data, message="Profil yangilandi"
        )
