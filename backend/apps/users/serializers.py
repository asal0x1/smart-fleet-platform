from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.validators import PhoneField

from .models import User, UserRole


def tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


def check_password_strength(value, user=None):
    """Django parol validatorlarini DRF xatosiga o'giradi."""
    try:
        validate_password(value, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return value


class RegisterSerializer(serializers.Serializer):
    phone = PhoneField()
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(
        choices=[UserRole.CLIENT, UserRole.DRIVER], default=UserRole.CLIENT
    )
    full_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_phone(self, value):
        # PhoneField allaqachon formatni tekshirib normalizatsiya qildi
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Bu telefon raqam allaqachon ro'yxatdan o'tgan"
            )
        return value

    def validate_password(self, value):
        return check_password_strength(value)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    phone = PhoneField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(phone=attrs["phone"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Telefon yoki parol noto'g'ri")
        if not user.is_active:
            raise serializers.ValidationError("Hisob bloklangan")
        attrs["user"] = user
        return attrs


class SendOTPSerializer(serializers.Serializer):
    phone = PhoneField()


class VerifyOTPSerializer(serializers.Serializer):
    phone = PhoneField()
    otp = serializers.RegexField(r"^\d{4,6}$", max_length=6)


class LogoutSerializer(serializers.Serializer):
    """Refresh token'ni blacklist'ga qo'shadi."""

    refresh_token = serializers.CharField()

    def validate_refresh_token(self, value):
        try:
            self.token = RefreshToken(value)
        except TokenError as exc:
            raise serializers.ValidationError(
                "Token yaroqsiz yoki muddati tugagan"
            ) from exc
        return value

    def save(self, **kwargs):
        self.token.blacklist()


class ChangePasswordSerializer(serializers.Serializer):
    """Kirgan foydalanuvchi o'z parolini o'zgartiradi."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri")
        return value

    def validate_new_password(self, value):
        return check_password_strength(value, user=self.context["request"].user)

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "Yangi parol eskisidan farq qilishi kerak"}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class ResetPasswordSerializer(serializers.Serializer):
    """OTP orqali parolni tiklash.

    Oqim:  POST send-otp/  ->  SMS keladi  ->  POST reset-password/
    """

    phone = PhoneField()
    otp = serializers.RegexField(r"^\d{4,6}$", max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_new_password(self, value):
        return check_password_strength(value)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "phone", "role", "full_name",
            "email", "avatar", "avatar_url", "is_verified", "created_at",
        ]
        read_only_fields = ["id", "phone", "role", "is_verified", "created_at"]
