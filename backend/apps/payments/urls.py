from django.urls import path

from .views import (
    ClickCompleteView,
    ClickPrepareView,
    ConfirmCashPaymentView,
    CreatePaymentView,
)

urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="payment-create"),
    path("click/prepare/", ClickPrepareView.as_view(), name="click-prepare"),
    path("click/complete/", ClickCompleteView.as_view(), name="click-complete"),
    path("<int:pk>/confirm-cash/", ConfirmCashPaymentView.as_view(),
         name="payment-confirm-cash"),
]
