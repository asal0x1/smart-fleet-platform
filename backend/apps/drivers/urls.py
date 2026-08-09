from django.urls import path

from .views import (
    DriverDocumentsView,
    DriverProfileView,
    NearbyDriversView,
    OnlineToggleView,
    UpdateLocationView,
)

urlpatterns = [
    path("profile/", DriverProfileView.as_view(), name="driver-profile"),
    path("documents/", DriverDocumentsView.as_view(), name="driver-documents"),
    path("location/", UpdateLocationView.as_view(), name="driver-location"),
    path("online/", OnlineToggleView.as_view(), name="driver-online"),
    path("nearby/", NearbyDriversView.as_view(), name="drivers-nearby"),
]
