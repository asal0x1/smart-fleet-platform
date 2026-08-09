from django.urls import path

from .consumers import NotificationConsumer, OrderConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/orders/<int:order_id>/", OrderConsumer.as_asgi()),
]
