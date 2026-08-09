from django.urls import path

from .views import (
    AvailableOrdersView,
    ChangeStatusView,
    EstimateView,
    OrderDetailView,
    OrderListCreateView,
    OrderReviewView,
    TariffListView,
)

urlpatterns = [
    path("tariffs/", TariffListView.as_view(), name="tariffs"),
    path("estimate/", EstimateView.as_view(), name="estimate"),
    path("available/", AvailableOrdersView.as_view(), name="available-orders"),
    path("", OrderListCreateView.as_view(), name="orders"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/status/", ChangeStatusView.as_view(), name="order-status"),
    path("<int:pk>/review/", OrderReviewView.as_view(), name="order-review"),
]
