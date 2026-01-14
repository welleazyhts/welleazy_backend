from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
import requests

from .models import User, PasswordResetToken, UserOTP
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordConfirmSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer, 
    UserSerializer
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {"id": user.id, "email": user.email, "name": user.name}
        }, status=status.HTTP_200_OK)


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)
        reset_token = PasswordResetToken.create_token(user)

        reset_link = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"

        send_mail(
            subject="Welleazy Password Reset",
            message=f"Hi {user.name or 'User'},\n\n"
                    f"Click the link below to reset your password:\n{reset_link}\n\n"
                    f"This link will expire in 15 minutes.\n\n"
                    f"Thanks,\nWelleazy Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": f"Reset link sent to {email}"}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_obj = serializer.validated_data["token_obj"]
        user = token_obj.user
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        token_obj.is_used = True
        token_obj.save()

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
       
class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.context["user"]
        method = serializer.context["method"]
        identifier = serializer.context["formatted_value"]  # formatted email or mobile

        otp_plain = UserOTP.create_otp(user, method, identifier)

        if method == "email":
            send_mail(
                subject="Your Login OTP",
                message=f"Hi {user.name or 'User'},\n\nYour OTP for login is {otp_plain}. "
                        f"This OTP will expire in 10 minutes.\n\nThanks,\nTeam",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[identifier],
                fail_silently=False,
            )
        else:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your login OTP is {otp_plain}. It expires in 10 minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=identifier,
            )

        return Response({"message": f"OTP sent to {method}: {identifier}"}, status=status.HTTP_200_OK)


# class RequestOTPView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = RequestOTPSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         user = serializer.context["user"]
#         method = serializer.context["method"]
#         identifier = serializer.context["formatted_value"]

#         otp_plain = UserOTP.create_otp(user, method, identifier)

#         if method == "email":
#             send_mail(
#                 subject="Your Login OTP",
#                 message=f"Hi {user.name or 'User'},\n\nYour OTP for login is {otp_plain}. "
#                         f"This OTP will expire in 10 minutes.\n\nThanks,\nTeam",
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[identifier],
#                 fail_silently=False,
#             )
#         else:
#             # --- FAST2SMS Integration ---
#             url = "https://www.fast2sms.com/dev/bulkV2"
#             payload = {
#                 "sender_id": settings.FAST2SMS_SENDER_ID,
#                 "message": f"Your login OTP is {otp_plain}. It expires in 10 minutes.",
#                 "language": settings.FAST2SMS_LANGUAGE,
#                 "route": settings.FAST2SMS_ROUTE,
#                 "numbers": identifier.replace("+91", ""),  # Fast2SMS expects plain mobile
#             }
#             headers = {
#                 "authorization": settings.FAST2SMS_API_KEY,
#                 "Content-Type": "application/x-www-form-urlencoded"
#             }

#             response = requests.post(url, data=payload, headers=headers)
#             if response.status_code != 200 or not response.json().get("return"):
#                 return Response(
#                     {"error": "Failed to send OTP via Fast2SMS", "details": response.text},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )

#         return Response(
#             {"message": f"OTP sent to {method}: {identifier}"},
#             status=status.HTTP_200_OK
#         )

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        otp_obj = serializer.validated_data["otp_obj"]

        otp_obj.is_used = True
        otp_obj.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "mobile_number": user.mobile_number,
                "name": user.name
            }
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user    

    def put(self, request, *args, **kwargs):
        # Treat PUT as partial update to avoid required field errors
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
class AdminLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user
        if not user.is_staff:
            return Response({"error": "Only admin users can log in here."}, status=status.HTTP_403_FORBIDDEN)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
