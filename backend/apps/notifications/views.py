from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import error_response, success_response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(ListAPIView):
    """GET /api/notifications/?is_read=false"""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        is_read = self.request.query_params.get("is_read")
        if is_read in ("true", "false"):
            qs = qs.filter(is_read=(is_read == "true"))
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["data"]["unread"] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return response


class NotificationReadView(APIView):
    """PATCH /api/notifications/{id}/read/  — bittasini o'qilgan qilish"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        updated = Notification.objects.filter(
            pk=pk, user=request.user
        ).update(is_read=True)
        if not updated:
            return error_response("Bildirishnoma topilmadi", status=404)
        return success_response(message="O'qilgan deb belgilandi")


class NotificationReadAllView(APIView):
    """PATCH /api/notifications/read-all/"""

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        n = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return success_response(data={"marked": n},
                                message=f"{n} ta bildirishnoma o'qildi")
