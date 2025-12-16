from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
from apps.location.models import City 

from .models import Test
from .serializers import TestSerializer

# from .models import DiagnosticCenter
# from .serializers import DiagnosticCenterSerializer

class TestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Test.objects.filter(deleted_at__isnull=True)
    serializer_class = TestSerializer

    def list(self, request):
        # Return list of tests (from external API or local DB).
        client_api_url = getattr(settings, "CLIENT_TEST_API_URL", None)

        # --- Optional: Fetch from Client API ---
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
                        "name": item.get("test_name") or item.get("name"),
                        "code": item.get("code"),
                        "description": item.get("description"),
                        "price": item.get("price"),
                    }
                    for item in data
                ]
                return Response(formatted_data, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch client API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        # --- Local DB Data ---
        queryset = self.get_queryset().order_by("id")
        serializer = TestSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        # Create a new test (for testing).
        serializer = TestSerializer(data=request.data)
        if serializer.is_valid():
            test = Test.objects.create(
                name=serializer.validated_data["name"],
                code=serializer.validated_data.get("code"),
                description=serializer.validated_data.get("description"),
                price=serializer.validated_data.get("price"),
                created_by=request.user,
                updated_by=request.user,
            )
            return Response(TestSerializer(test).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class DiagnosticCenterViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     queryset = DiagnosticCenter.objects.filter(deleted_at__isnull=True)
#     serializer_class = DiagnosticCenterSerializer

#     def list(self, request):
#         """Return list of diagnostic centers (from external API or local DB)."""
#         client_api_url = getattr(settings, "CLIENT_DIAGNOSTIC_API_URL", None)

#         if client_api_url:
#             try:
#                 headers = {}
#                 client_api_token = getattr(settings, "CLIENT_API_TOKEN", None)
#                 if client_api_token:
#                     headers["Authorization"] = f"Bearer {client_api_token}"

#                 response = requests.get(client_api_url, headers=headers, timeout=10)
#                 response.raise_for_status()
#                 data = response.json()

#                 formatted_data = [
#                     {
#                         "id": item.get("id"),
#                         "name": item.get("center_name") or item.get("name"),
#                         "code": item.get("code"),
#                         "address": item.get("address"),
#                         "area": item.get("area"),
#                         "pincode": item.get("pincode"),
#                         "contact_number": item.get("contact_number"),
#                         "email": item.get("email"),
#                         "active": item.get("active", True),
#                     }
#                     for item in data
#                 ]

#                 return Response(formatted_data, status=status.HTTP_200_OK)

#             except requests.RequestException as e:
#                 return Response(
#                     {"error": f"Failed to fetch external API: {e}"},
#                     status=status.HTTP_502_BAD_GATEWAY,
#                 )

#         queryset = self.get_queryset().order_by("id")
#         serializer = DiagnosticCenterSerializer(queryset, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def create(self, request):
#         """Create new diagnostic center."""
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         center = serializer.save(created_by=request.user, updated_by=request.user)
#         return Response(DiagnosticCenterSerializer(center).data, status=status.HTTP_201_CREATED)
  
# class DiagnosticCenterSearchAPIView(APIView):

    def post(self, request):
        city_id = request.data.get("city_id")
        test_ids = request.data.get("test_ids", [])

        if not city_id or not test_ids:
            return Response(
                {"detail": "City and at least one test are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            city = City.objects.get(id=city_id)
        except City.DoesNotExist:
            return Response(
                {"detail": "City not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Find diagnostic centers in the city that have *all* the tests
        diagnostic_centers = (
            DiagnosticCenter.objects.filter(city=city, tests__in=test_ids)
            .distinct()
        )

        # Filter to those that have *all* selected tests
        diagnostic_centers = [
            dc for dc in diagnostic_centers
            if set(test_ids).issubset(set(dc.tests.values_list("id", flat=True)))
        ]

        if not diagnostic_centers:
            return Response(
                {
                    "detail": "No diagnostic centers available for these selected tests or test combination. "
                              "We appreciate your understanding, we are working to expand our coverage soon."
                },
                status=status.HTTP_200_OK
            )

        serializer = DiagnosticCenterSerializer(diagnostic_centers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)