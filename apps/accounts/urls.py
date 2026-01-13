from django.urls import path
from .views import (
    RegisterView,
    RequestPasswordResetView,
    ResetPasswordConfirmView,
    RequestOTPView,
    VerifyOTPView,
    LogoutView,
    CustomTokenObtainPairView, 
    UserProfileView,
    AdminLoginView
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('password-login/', CustomTokenObtainPairView.as_view(), name='password-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('request-reset/', RequestPasswordResetView.as_view(), name='request-reset'),
    path('reset-confirm/', ResetPasswordConfirmView.as_view(), name='reset-confirm'),
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('otp-login/', VerifyOTPView.as_view(), name='otp-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
]
