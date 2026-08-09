"""Role asosidagi ruxsatlar (dokdagi authorize middleware ekvivalenti)."""
from rest_framework.permissions import BasePermission


class IsClient(BasePermission):
    message = "Faqat mijozlar uchun."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "client"
        )


class IsDriver(BasePermission):
    message = "Faqat haydovchilar uchun."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "driver"
        )


class IsAdminRole(BasePermission):
    message = "Faqat administratorlar uchun."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == "admin" or request.user.is_staff)
        )
