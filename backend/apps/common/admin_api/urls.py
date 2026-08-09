"""Admin panel API marshrutlari.

config/urls.py da shunday ulanadi:
    path("admin/", include("apps.common.admin_api.urls")),
Natijada barcha URL'lar /api/admin/... bo'ladi.
"""
from django.urls import path

from . import views

app_name = "admin_api"

urlpatterns = [
    # --- Statistika ---
    path("stats/", views.DashboardStatsView.as_view(), name="stats"),
    path("stats/revenue/", views.RevenueStatsView.as_view(), name="stats-revenue"),

    # --- Foydalanuvchilar ---
    path("users/", views.AdminUserListView.as_view(), name="users"),
    path("users/<int:pk>/", views.AdminUserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/block/", views.AdminUserBlockView.as_view(), name="user-block"),

    # --- Haydovchilar ---
    path("drivers/", views.AdminDriverListView.as_view(), name="drivers"),
    path("drivers/<int:pk>/", views.AdminDriverDetailView.as_view(), name="driver-detail"),
    path("drivers/<int:pk>/approve/", views.AdminDriverApproveView.as_view(), name="driver-approve"),
    path("drivers/<int:pk>/block/", views.AdminDriverBlockView.as_view(), name="driver-block"),

    # --- Buyurtmalar ---
    path("orders/", views.AdminOrderListView.as_view(), name="orders"),
    path("orders/<int:pk>/", views.AdminOrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/cancel/", views.AdminOrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/assign/", views.AdminOrderAssignDriverView.as_view(), name="order-assign"),

    # --- Tariflar (CRUD) ---
    path("tariffs/", views.AdminTariffListCreateView.as_view(), name="tariffs"),
    path("tariffs/<int:pk>/", views.AdminTariffDetailView.as_view(), name="tariff-detail"),

    # --- To'lovlar ---
    path("payments/", views.AdminPaymentListView.as_view(), name="payments"),

    # --- So'rovlar: og'ir texnika ---
    path("requests/heavy/", views.AdminHeavyRequestListView.as_view(), name="heavy-requests"),
    path("requests/heavy/<int:pk>/", views.AdminHeavyRequestDetailView.as_view(), name="heavy-request-detail"),
    path("requests/heavy/<int:pk>/status/", views.AdminHeavyRequestStatusView.as_view(), name="heavy-request-status"),

    # --- So'rovlar: to'y transporti ---
    path("requests/wedding/", views.AdminWeddingRequestListView.as_view(), name="wedding-requests"),
    path("requests/wedding/<int:pk>/", views.AdminWeddingRequestDetailView.as_view(), name="wedding-request-detail"),
    path("requests/wedding/<int:pk>/status/", views.AdminWeddingRequestStatusView.as_view(), name="wedding-request-status"),
]
