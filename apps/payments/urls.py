from django.urls import path
from .views import (
    CreateRazorpayOrderAPIView, 
    RazorpayVerifyPaymentAPIView, 
    RazorpayPaymentPageView,
    MyTransactionsAPIView
)

urlpatterns = [
    path("create-order/<int:cart_id>/", CreateRazorpayOrderAPIView.as_view()),
    path("verify/", RazorpayVerifyPaymentAPIView.as_view()),
    path("pay/<int:cart_id>/", RazorpayPaymentPageView.as_view(), name="razorpay-pay-page"),
    path("my-transactions/", MyTransactionsAPIView.as_view()),
]
