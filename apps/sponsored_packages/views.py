from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.utils import timezone
import requests

from .models import SponsoredPackage
from .serializers import SponsoredPackageSerializer

class SponsoredPackageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = SponsoredPackage.objects.filter(deleted_at__isnull=True)
    serializer_class = SponsoredPackageSerializer

    def list(self, request):
        #List sponsored packages (optionally from external API).
        client_api_url = getattr(settings, "CLIENT_SPONSORED_PACKAGE_API_URL", None)
        if client_api_url:
            try:
                headers = {}
                token = getattr(settings, "CLIENT_API_TOKEN", None)
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                response = requests.get(client_api_url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                formatted = [
                    {
                        "id": item.get("id"),
                        "name": item.get("package_name") or item.get("name"),
                        "description": item.get("description"),
                        "price": item.get("price"),
                        "validity_till": item.get("validity_till"),
                    }
                    for item in data
                ]
                return Response(formatted, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch external API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        queryset = self.get_queryset().order_by("id")
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        package = serializer.save(created_by=request.user, updated_by=request.user)
        return Response(self.serializer_class(package).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        return Response(
            {
                "message": "Sponsored package updated successfully",
                "data": response.data
            },
            status=status.HTTP_200_OK
        )
        
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)

        return Response(
            {
                "message": "Sponsored package updated successfully",
                "data": response.data
            },
            status=status.HTTP_200_OK
        )
        
    def destroy(self, request, *args, **kwargs):
        package = self.get_object()
        package.deleted_at = timezone.now()
        package.save(update_fields=["deleted_at"])

        return Response(
            {"message": "Sponsored package deleted successfully"},
            status=status.HTTP_200_OK
        )
