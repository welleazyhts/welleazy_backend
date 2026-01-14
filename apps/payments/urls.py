from django.urls import path
from .views import (
    CreateRazorpayOrderAPIView, 
    RazorpayVerifyPaymentAPIView, 
    RazorpayPaymentPageView,
    MyTransactionsAPIView
)

urlpatterns = [
    path("create-order/<int:cart_id>/", CreateRazorpayOrderAPIView.as_view(), name="razorpay-create-order"),
    path("verify/", RazorpayVerifyPaymentAPIView.as_view(), name="razorpay-verify"),
    path("pay/<int:cart_id>/", RazorpayPaymentPageView.as_view(), name="razorpay-pay-page"),
    path("my-transactions/", MyTransactionsAPIView.as_view()),
]
