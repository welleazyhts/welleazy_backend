from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import VisitType
from .serializers import VisitTypeSerializer
import requests
from rest_framework.generics import ListAPIView
from django.db.models import Min, Max
from apps.diagnostic_center.models import DiagnosticCenter
from apps.diagnostic_center.serializers import DiagnosticCenterSerializer

class VisitTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = VisitTypeSerializer
    queryset = VisitType.objects.filter(deleted_at__isnull=True)

    def list(self, request):
        #Return list of visit types.
        client_api_url = getattr(settings, "CLIENT_VISIT_TYPE_API_URL", None)

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
                        "name": item.get("name"),
                    }
                    for item in data
                ]
                return Response(formatted_data, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch client API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        # Fallback to local DB
        queryset = self.get_queryset().order_by("id")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        #Create a new visit type.
        serializer = VisitTypeSerializer(data=request.data)
        if serializer.is_valid():
            visit_type = VisitType.objects.create(
                name=serializer.validated_data["name"],
                created_by=request.user,
                updated_by=request.user,    
            )
            return Response(VisitTypeSerializer(visit_type).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DiagnosticCenterFilterAPIView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = DiagnosticCenterSerializer

    def get_queryset(self):
        queryset = DiagnosticCenter.objects.filter(active=True, deleted_at__isnull=True)

        # --- Filters ---
        pincode = self.request.query_params.get("pincode")
        area = self.request.query_params.get("area")
        name = self.request.query_params.get("name")
        visit_type = self.request.query_params.get("visit_type")
        test_ids = self.request.query_params.get("test_ids")
        sort_price = self.request.query_params.get("sort_price")  # "low" or "high"

        if pincode:
            queryset = queryset.filter(pincode__iexact=pincode)

        if area:
            queryset = queryset.filter(area__icontains=area)

        if name:
            queryset = queryset.filter(name__icontains=name)

        if visit_type:
            queryset = queryset.filter(visit_types__id=visit_type)

        if test_ids:
            # Assume test_ids is a comma-separated string of IDs
            try:
                id_list = [id.strip() for id in test_ids.split(",") if id.strip()]
                if id_list:
                    # Filter DCs that have ALL of the selected tests
                    for tid in id_list:
                        queryset = queryset.filter(tests__id=tid)
            except ValueError:
                pass

        # --- Sorting by price (lowest or highest) ---
        if sort_price:
            if sort_price.lower() == "low":
                queryset = queryset.annotate(min_price=Min("tests__price")).order_by("min_price")
            elif sort_price.lower() == "high":
                queryset = queryset.annotate(max_price=Max("tests__price")).order_by("-max_price")

        queryset = queryset.distinct()
        return queryset