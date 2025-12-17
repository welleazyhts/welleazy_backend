from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests

from apps.diagnostic_center.models import DiagnosticCenter
from apps.diagnostic_center.serializers import DiagnosticCenterSerializer
from apps.location.models import City

from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from apps.diagnostic_center.filters import DiagnosticCenterFilter

class DiagnosticCenterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = DiagnosticCenter.objects.filter(deleted_at__isnull=True)
    serializer_class = DiagnosticCenterSerializer

    def list(self, request):
        client_api_url = getattr(settings, "CLIENT_DIAGNOSTIC_API_URL", None)
        if client_api_url:
            try:
                headers = {}
                client_api_token = getattr(settings, "CLIENT_API_TOKEN", None)
                if client_api_token:
                    headers["Authorization"] = f"Bearer {client_api_token}"

                response = requests.get(client_api_url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                formatted_data = [
                    {
                        "id": item.get("id"),
                        "name": item.get("center_name") or item.get("name"),
                        "code": item.get("code"),
                        "address": item.get("address"),
                        "area": item.get("area"),
                        "pincode": item.get("pincode"),
                        "contact_number": item.get("contact_number"),
                        "email": item.get("email"),
                        "active": item.get("active", True),
                    }
                    for item in data
                ]
                return Response(formatted_data, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch external API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        queryset = self.get_queryset().order_by("id")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        center = serializer.save(created_by=request.user, updated_by=request.user)
        return Response(
            {
                "message": "Diagnostic center created successfully",
                "data": self.get_serializer(center).data
            },
            status=status.HTTP_201_CREATED
        )
        
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Diagnostic center updated successfully",
                "data": response.data
            },
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response(
            {
                "message": "Diagnostic center partially updated successfully",
                "data": response.data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {
                "message": "Diagnostic center deleted successfully"
            },
            status=status.HTTP_200_OK
        )


class DiagnosticCenterSearchAPIView(generics.ListAPIView):
    queryset = DiagnosticCenter.objects.filter(deleted_at__isnull=True).distinct()
    serializer_class = DiagnosticCenterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DiagnosticCenterFilter
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        return super().list(request, *args, **kwargs)

