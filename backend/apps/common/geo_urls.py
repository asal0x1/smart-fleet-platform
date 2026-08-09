from django.urls import path

from .geo_views import GeocodeView, ReverseGeocodeView

urlpatterns = [
    path("", GeocodeView.as_view(), name="geocode"),
    path("reverse/", ReverseGeocodeView.as_view(), name="geocode-reverse"),
]
