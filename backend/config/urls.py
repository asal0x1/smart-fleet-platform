"""SMART FLEET — root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

api_v1 = [
    path("auth/", include("apps.users.urls")),
    path("drivers/", include("apps.drivers.urls")),
    path("orders/", include("apps.orders.urls")),
    path("payments/", include("apps.payments.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("geocode/", include("apps.common.geo_urls")),
    # Admin panel (frontend) API — /api/admin/...
    path("admin/", include("apps.common.admin_api.urls")),
    path("", include("apps.requests.urls")),  # heavy-equipment/ + wedding/
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include((api_v1, "api"))),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
