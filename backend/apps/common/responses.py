"""
Bir xil javob formati:
    {"success": true, "message": ..., "data": {...}}
    {"success": false, "message": ..., "errors": {...}}
"""
from rest_framework.response import Response


def success_response(data=None, message=None, status=200):
    payload = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status)


def error_response(message, errors=None, status=400):
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status)
