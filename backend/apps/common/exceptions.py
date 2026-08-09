"""DRF xatolarini {"success": false, ...} formatiga o'girish."""
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    detail = response.data
    message = "Xatolik yuz berdi"
    errors = None

    if isinstance(detail, dict):
        # {"detail": "..."} yoki field-based validation errors
        if "detail" in detail and len(detail) == 1:
            message = str(detail["detail"])
        else:
            message = "Ma'lumotlar noto'g'ri"
            errors = detail
    elif isinstance(detail, list):
        errors = {"non_field_errors": detail}
        message = "Ma'lumotlar noto'g'ri"

    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors

    response.data = payload
    return response
