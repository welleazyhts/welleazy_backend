from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import Q
import requests

from apps.diagnostic_center.models import DiagnosticCenter, DCContact, DCDocument
from apps.diagnostic_center.serializers import (
    DiagnosticCenterSerializer, DiagnosticCenterListSerializer,
    DiagnosticCenterDetailSerializer, DiagnosticCenterCreateSerializer,
    DCContactSerializer, DCDocumentSerializer
)
from apps.location.models import City
from apps.consultation_filter.models import Vendor

from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage


class DiagnosticCenterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = DiagnosticCenter.objects.filter(deleted_at__isnull=True, active=True)
    serializer_class = DiagnosticCenterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'city': ['exact'],
        'vendor': ['exact', 'isnull'],
        'grade': ['exact', 'in'],
        'home_collection': ['exact'],
        'is_nabl_accredited': ['exact'],
        'active': ['exact'],
    }
    search_fields = ['name', 'code', 'area', 'pincode']
    ordering_fields = ['name', 'grade', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return DiagnosticCenterListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return DiagnosticCenterCreateSerializer
        return DiagnosticCenterDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related('city', 'vendor')

        # For detail view, prefetch related objects
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'contacts', 'documents', 'dc_tests', 'tests', 'visit_types'
            )

        # Filter by vendor code (e.g., ?vendor_code=APOLLO)
        vendor_code = self.request.query_params.get('vendor_code')
        if vendor_code:
            queryset = queryset.filter(vendor__code__iexact=vendor_code)

        # Filter by multiple vendor IDs (e.g., ?vendor_ids=1,2,3)
        vendor_ids = self.request.query_params.get('vendor_ids')
        if vendor_ids:
            vendor_id_list = [int(v) for v in vendor_ids.split(',') if v.isdigit()]
            queryset = queryset.filter(vendor_id__in=vendor_id_list)

        # Filter by center_status
        center_status = self.request.query_params.get('center_status')
        if center_status:
            queryset = queryset.filter(center_status=center_status)

        # Filter by provider_type
        provider_type = self.request.query_params.get('provider_type')
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)

        # Filter by test availability
        test_id = self.request.query_params.get('test_id')
        if test_id:
            queryset = queryset.filter(tests__id=test_id)

        # Filter by package availability
        package_id = self.request.query_params.get('health_package_id')
        if package_id:
            queryset = queryset.filter(health_packages__id=package_id)

        return queryset.distinct()

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

    # Contact management actions
    @action(detail=True, methods=['get', 'post'])
    def contacts(self, request, pk=None):
        """List or add contacts for a DC"""
        dc = self.get_object()
        if request.method == 'GET':
            contacts = dc.contacts.all()
            serializer = DCContactSerializer(contacts, many=True)
            return Response(serializer.data)
        else:
            serializer = DCContactSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(diagnostic_center=dc)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'delete'], url_path='contacts/(?P<contact_id>[^/.]+)')
    def contact_detail(self, request, pk=None, contact_id=None):
        """Update or delete a specific contact"""
        dc = self.get_object()
        try:
            contact = dc.contacts.get(id=contact_id)
        except DCContact.DoesNotExist:
            return Response({'error': 'Contact not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            contact.delete()
            return Response({'message': 'Contact deleted'}, status=status.HTTP_200_OK)
        else:
            serializer = DCContactSerializer(contact, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    # Document management actions
    @action(detail=True, methods=['get', 'post'])
    def documents(self, request, pk=None):
        """List or add documents for a DC"""
        dc = self.get_object()
        if request.method == 'GET':
            documents = dc.documents.all()
            serializer = DCDocumentSerializer(documents, many=True)
            return Response(serializer.data)
        else:
            serializer = DCDocumentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(diagnostic_center=dc)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='documents/(?P<doc_id>[^/.]+)/verify')
    def verify_document(self, request, pk=None, doc_id=None):
        """Verify a document"""
        from django.utils import timezone
        dc = self.get_object()
        try:
            document = dc.documents.get(id=doc_id)
        except DCDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        document.is_verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        return Response({'message': 'Document verified', 'data': DCDocumentSerializer(document).data})


class DiagnosticCenterSearchAPIView(APIView):
    """
    Search for diagnostic centers with various filters including vendor.
    """

    VALID_KEYS = {
        "city_id",
        "test_ids",
        "health_package_id",
        "sponsored_package_id",
        "vendor_id",
        "vendor_ids",
        "vendor_code",
        "home_collection",
        "grade",
    }

    def post(self, request):

        # validate keys
        received_keys = set(request.data.keys())
        invalid_keys = received_keys - self.VALID_KEYS

        if invalid_keys:
            suggestions = {}
            for invalid in invalid_keys:
                close = self.get_close_key(invalid)
                if close:
                    suggestions[invalid] = f"Did you mean '{close}'?"

            response = {
                "detail": f"Invalid parameters: {', '.join(invalid_keys)}"
            }
            if suggestions:
                response["suggestions"] = suggestions

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        city_id = request.data.get("city_id")
        test_ids = request.data.get("test_ids", [])
        health_package_id = request.data.get("health_package_id")
        sponsored_package_id = request.data.get("sponsored_package_id")
        vendor_id = request.data.get("vendor_id")
        vendor_ids = request.data.get("vendor_ids", [])
        vendor_code = request.data.get("vendor_code")
        home_collection = request.data.get("home_collection")
        grade = request.data.get("grade")

        if not city_id:
            return Response({"detail": "City is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = City.objects.get(id=city_id)
        except City.DoesNotExist:
            return Response({"detail": "City not found."}, status=status.HTTP_404_NOT_FOUND)

        diagnostic_centers = DiagnosticCenter.objects.filter(city=city, active=True).select_related('vendor').distinct()

        # Vendor filters
        if vendor_id:
            diagnostic_centers = diagnostic_centers.filter(vendor_id=vendor_id)
        elif vendor_ids:
            diagnostic_centers = diagnostic_centers.filter(vendor_id__in=vendor_ids)
        elif vendor_code:
            diagnostic_centers = diagnostic_centers.filter(vendor__code__iexact=vendor_code)

        # Home collection filter
        if home_collection is not None:
            diagnostic_centers = diagnostic_centers.filter(home_collection=home_collection)

        # Grade filter
        if grade:
            diagnostic_centers = diagnostic_centers.filter(grade=grade)

        if health_package_id:
            diagnostic_centers = diagnostic_centers.filter(health_packages__id=health_package_id)

        if sponsored_package_id:
            diagnostic_centers = diagnostic_centers.filter(sponsored_packages__id=sponsored_package_id)

        if test_ids:
            test_ids = [int(tid) for tid in test_ids if str(tid).isdigit()]
            diagnostic_centers = diagnostic_centers.filter(tests__in=test_ids).distinct()
            diagnostic_centers = [
                dc for dc in diagnostic_centers
                if set(test_ids).issubset(set(dc.tests.values_list("id", flat=True)))
            ]

        if not diagnostic_centers:
            return Response(
                {"detail": "No diagnostic centers found for the selected filters."},
                status=status.HTTP_200_OK
            )

        # Return detailed response with vendor info
        if hasattr(diagnostic_centers, "values"):
            centers = list(diagnostic_centers.values(
                "id", "name", "code", "address", "area", "pincode",
                "home_collection", "home_collection_charge", "grade",
                "vendor_id", "vendor__name", "vendor__code"
            ))
            # Clean up vendor field names
            for center in centers:
                center["vendor_name"] = center.pop("vendor__name", None)
                center["vendor_code"] = center.pop("vendor__code", None)
        else:
            centers = [
                {
                    "id": dc.id,
                    "name": dc.name,
                    "code": dc.code,
                    "address": dc.address,
                    "area": dc.area,
                    "pincode": dc.pincode,
                    "home_collection": dc.home_collection,
                    "home_collection_charge": float(dc.home_collection_charge) if dc.home_collection_charge else 0,
                    "grade": dc.grade,
                    "vendor_id": dc.vendor_id,
                    "vendor_name": dc.vendor.name if dc.vendor else None,
                    "vendor_code": dc.vendor.code if dc.vendor else None,
                }
                for dc in diagnostic_centers
            ]

        return Response({"centers": centers, "count": len(centers)}, status=status.HTTP_200_OK)

    def get_close_key(self, invalid_key):
        from difflib import get_close_matches
        matches = get_close_matches(invalid_key, self.VALID_KEYS, n=1, cutoff=0.6)
        return matches[0] if matches else None
