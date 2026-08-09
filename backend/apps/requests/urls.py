from django.urls import path

from .views import (
    BusRequestView,
    GiftMemorialRequestView,
    HeavyEquipmentRequestView,
    MyBusRequestsView,
    MyGiftMemorialRequestsView,
    MyHeavyEquipmentRequestsView,
    MyPersonalDriverRequestsView,
    MyWeddingRequestsView,
    PersonalDriverRequestView,
    WeddingRequestView,
)

urlpatterns = [
    path("heavy-equipment/requests/", HeavyEquipmentRequestView.as_view(), name="heavy-request"),
    path("heavy-equipment/requests/mine/", MyHeavyEquipmentRequestsView.as_view(), name="heavy-request-mine"),
    path("wedding/requests/", WeddingRequestView.as_view(), name="wedding-request"),
    path("wedding/requests/mine/", MyWeddingRequestsView.as_view(), name="wedding-request-mine"),
    path("personal-driver/requests/", PersonalDriverRequestView.as_view(), name="personal-driver-request"),
    path("personal-driver/requests/mine/", MyPersonalDriverRequestsView.as_view(), name="personal-driver-request-mine"),
    path("bus/requests/", BusRequestView.as_view(), name="bus-request"),
    path("bus/requests/mine/", MyBusRequestsView.as_view(), name="bus-request-mine"),
    path("gift-memorial/requests/", GiftMemorialRequestView.as_view(), name="gift-memorial-request"),
    path("gift-memorial/requests/mine/", MyGiftMemorialRequestsView.as_view(), name="gift-memorial-request-mine"),
]
