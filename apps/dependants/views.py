from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Dependant, RelationshipType, ProfileSwitch
from .serializers import (
    DependantSerializer, 
    RelationshipTypeSerializer,
    SwitchProfileRequestSerializer,
    VerifySwitchOTPSerializer,
    ActiveProfileSerializer
)
from apps.notifications.utils import notify_user

class RelationshipTypeListCreateView(generics.ListCreateAPIView):
    queryset = RelationshipType.objects.all()
    serializer_class = RelationshipTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class DependantListCreateView(generics.ListCreateAPIView):
    serializer_class = DependantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Dependant.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "Dependant added successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def perform_create(self, serializer):
        dependant=serializer.save(created_by=self.request.user,
            updated_by=self.request.user)
        
        notify_user(
            self.request.user,
            "Dependant Added",
            f"{dependant.name} was added as your family member.",
            item_type="dependant"
        )   # FIXED: Do NOT pass user



class DependantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DependantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Dependant.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Dependant updated successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Dependant deleted successfully"},
            status=200
        )


# Switch Profile Views

class SwitchProfileRequestView(APIView):
    #Request to switch to a dependant's profile - generates and sends OTP.
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SwitchProfileRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifySwitchOTPView(APIView):
    #Verify OTP and activate profile switch.
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VerifySwitchOTPSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetActiveProfileView(APIView):
    #Get the current active profile (main user or switched dependant).
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ActiveProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SwitchBackView(APIView):
    #Switch back to main user profile.
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        active_switch = ProfileSwitch.get_active_switch(request.user)
        
        if not active_switch:
            return Response(
                {"message": "You are already on your main profile."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        active_switch.deactivate()
        
        return Response(
            {
                "message": "Successfully switched back to your main profile.",
                "profile_type": "self"
            },
            status=status.HTTP_200_OK
        )

