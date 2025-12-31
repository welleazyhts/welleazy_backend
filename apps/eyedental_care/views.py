from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from rest_framework import viewsets, permissions, status, filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from .models import (
    EyeDentalService,
    EyeTreatment, DentalTreatment,
    EyeVendorAddress, DentalVendorAddress,
    EyeDentalVoucher, EyeDentalVoucherRemark
)
from .serializers import (
    EyeDentalServiceSerializer,
    EyeTreatmentSerializer, DentalTreatmentSerializer,
    EyeVendorSerializer, DentalVendorSerializer,
    EyeDentalVoucherCreateSerializer, EyeDentalVoucherSerializer,
    EyeDentalVoucherRemarkSerializer,
    EyeDentalVoucherAdminSerializer, EyeDentalVoucherAdminUpdateSerializer
)


class SmallPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargePagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 500


# ---------------------------------------
#  SERVICE PROGRAM VIEWSETS
# ---------------------------------------
class EyeDentalServiceViewSet(ModelViewSet):
    """
    ViewSet for Eye/Dental Service Programs - Public access for listing
    """
    queryset = EyeDentalService.objects.filter(is_active=True)
    serializer_class = EyeDentalServiceSerializer
    pagination_class = SmallPagination
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = EyeDentalService.objects.filter(is_active=True)

        # Filter by service type (eye/dental)
        service_type = self.request.query_params.get('service_type', None)
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        return queryset.order_by('display_order', 'name')


# ---------------------------------------
#  TREATMENT VIEWSETS
# ---------------------------------------
class EyeTreatmentViewSet(ModelViewSet):
    """
    ViewSet for Eye Treatments - Public access for listing
    """
    queryset = EyeTreatment.objects.filter(is_active=True)
    serializer_class = EyeTreatmentSerializer
    pagination_class = SmallPagination
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class DentalTreatmentViewSet(ModelViewSet):
    """
    ViewSet for Dental Treatments - Public access for listing
    """
    queryset = DentalTreatment.objects.filter(is_active=True)
    serializer_class = DentalTreatmentSerializer
    pagination_class = SmallPagination
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


# ---------------------------------------
#  VENDOR VIEWSETS
# ---------------------------------------
class EyeVendorAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Eye Care Vendors - Public access for listing
    Supports filtering by city, state, treatment, and pincode
    """
    queryset = EyeVendorAddress.objects.filter(is_active=True).select_related('vendor', 'city', 'state')
    serializer_class = EyeVendorSerializer
    pagination_class = SmallPagination
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = EyeVendorAddress.objects.filter(is_active=True).select_related('vendor', 'city', 'state')

        # Filter by city name or ID
        city = self.request.query_params.get('city', None)
        city_id = self.request.query_params.get('city_id', None)
        if city:
            queryset = queryset.filter(city__name__icontains=city)
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        # Filter by state name or ID
        state = self.request.query_params.get('state', None)
        state_id = self.request.query_params.get('state_id', None)
        if state:
            queryset = queryset.filter(state__name__icontains=state)
        if state_id:
            queryset = queryset.filter(state_id=state_id)

        # Filter by treatment
        treatment = self.request.query_params.get('treatment', None)
        if treatment:
            queryset = queryset.filter(treatments__id=treatment)

        # Filter by pincode
        pincode = self.request.query_params.get('pincode', None)
        if pincode:
            queryset = queryset.filter(pincode=pincode)

        # Search by name/address
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(vendor__name__icontains=search) |
                Q(address__icontains=search)
            )

        return queryset.distinct().prefetch_related('treatments')


class DentalVendorAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dental Care Vendors - Public access for listing
    Supports filtering by city, state, treatment, and pincode
    """
    queryset = DentalVendorAddress.objects.filter(is_active=True).select_related('vendor', 'city', 'state')
    serializer_class = DentalVendorSerializer
    pagination_class = SmallPagination
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = DentalVendorAddress.objects.filter(is_active=True).select_related('vendor', 'city', 'state')

        # Filter by city name or ID
        city = self.request.query_params.get('city', None)
        city_id = self.request.query_params.get('city_id', None)
        if city:
            queryset = queryset.filter(city__name__icontains=city)
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        # Filter by state name or ID
        state = self.request.query_params.get('state', None)
        state_id = self.request.query_params.get('state_id', None)
        if state:
            queryset = queryset.filter(state__name__icontains=state)
        if state_id:
            queryset = queryset.filter(state_id=state_id)

        # Filter by treatment
        treatment = self.request.query_params.get('treatment', None)
        if treatment:
            queryset = queryset.filter(treatments__id=treatment)

        # Filter by pincode
        pincode = self.request.query_params.get('pincode', None)
        if pincode:
            queryset = queryset.filter(pincode=pincode)

        # Search by name/address
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(vendor__name__icontains=search) |
                Q(address__icontains=search)
            )

        return queryset.distinct().prefetch_related('treatments')


# ---------------------------------------
#  VOUCHER VIEWSETS (Customer)
# ---------------------------------------
class EyeDentalVoucherViewSet(ModelViewSet):
    """
    ViewSet for Eye/Dental Vouchers - Authenticated users only
    """
    queryset = EyeDentalVoucher.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]
    pagination_class = SmallPagination

    def get_serializer_class(self):
        if self.action == "create":
            return EyeDentalVoucherCreateSerializer
        return EyeDentalVoucherSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = EyeDentalVoucher.objects.filter(user=user).order_by("-created_at")

        # Filter by service type
        service_type = self.request.query_params.get('service_type', None)
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related(
            'eye_treatment', 'dental_treatment',
            'eye_vendor', 'dental_vendor'
        ).prefetch_related('remarks')

    def retrieve(self, request, *args, **kwargs):
        voucher = self.get_object()

        if voucher.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not own this voucher"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(voucher)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        voucher = self.get_object()
        if voucher.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not own this voucher"}, status=status.HTTP_403_FORBIDDEN)

        if voucher.status not in ['fresh', 'pending']:
            return Response(
                {"detail": f"Cannot activate voucher with status: {voucher.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        voucher.status = 'active'
        voucher.activated_at = timezone.now()
        voucher.save()

        return Response({
            'status': 'activated',
            'voucher_id': voucher.request_id
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        voucher = self.get_object()
        if voucher.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not own this voucher"}, status=status.HTTP_403_FORBIDDEN)

        if voucher.status in ['cancelled', 'completed']:
            return Response(
                {"detail": f"Cannot cancel voucher with status: {voucher.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        voucher.status = 'cancelled'
        voucher.save()

        return Response({'status': 'cancelled'})


# ---------------------------------------
#  ADMIN VIEWSETS
# ---------------------------------------
class EyeDentalVoucherAdminViewSet(ModelViewSet):
    """
    Admin ViewSet for Eye/Dental Voucher Case Management
    - Full CRUD operations on all cases
    - Search, filter, and export capabilities
    - Remarks/notes management
    """
    queryset = EyeDentalVoucher.objects.all().order_by("-created_at")
    permission_classes = [IsAdminUser]
    pagination_class = LargePagination

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return EyeDentalVoucherAdminUpdateSerializer
        return EyeDentalVoucherAdminSerializer

    def get_queryset(self):
        queryset = EyeDentalVoucher.objects.all().order_by("-created_at")

        # Filter by service type
        service_type = self.request.query_params.get('service_type', None)
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by booking_for (self/dependant)
        booking_for = self.request.query_params.get('booking_for', None)
        if booking_for:
            queryset = queryset.filter(booking_for=booking_for)

        # Filter by corporate
        corporate_id = self.request.query_params.get('corporate_id', None)
        if corporate_id:
            queryset = queryset.filter(corporate_id=corporate_id)

        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        # Search by request_id, name, email, contact
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(request_id__icontains=search) |
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(contact_number__icontains=search) |
                Q(vendor_name_snapshot__icontains=search)
            )

        return queryset.select_related(
            'user', 'eye_treatment', 'dental_treatment',
            'eye_vendor', 'dental_vendor', 'updated_by'
        ).prefetch_related('remarks')

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def add_remark(self, request, pk=None):
        """Add a remark/note to a voucher case"""
        voucher = self.get_object()
        remark_text = request.data.get('remark', '')

        if not remark_text:
            return Response(
                {"detail": "Remark text is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        remark = EyeDentalVoucherRemark.objects.create(
            voucher=voucher,
            remark=remark_text,
            created_by=request.user
        )

        serializer = EyeDentalVoucherRemarkSerializer(remark)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Update voucher status with optional remark"""
        voucher = self.get_object()
        new_status = request.data.get('status', None)
        remark_text = request.data.get('remark', '')

        if not new_status:
            return Response(
                {"detail": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = [s[0] for s in EyeDentalVoucher.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"Invalid status. Choose from: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = voucher.status
        voucher.status = new_status
        voucher.updated_by = request.user

        if new_status == 'active' and not voucher.activated_at:
            voucher.activated_at = timezone.now()

        voucher.save()

        # Add status change remark
        remark_content = f"Status changed from '{old_status}' to '{new_status}'."
        if remark_text:
            remark_content += f" Note: {remark_text}"

        EyeDentalVoucherRemark.objects.create(
            voucher=voucher,
            remark=remark_content,
            created_by=request.user
        )

        serializer = EyeDentalVoucherAdminSerializer(voucher)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def statistics(self, request):
        """Get statistics for dashboard"""
        from django.db.models import Count

        total = EyeDentalVoucher.objects.count()
        by_status = EyeDentalVoucher.objects.values('status').annotate(count=Count('id'))
        by_service = EyeDentalVoucher.objects.values('service_type').annotate(count=Count('id'))

        # Today's cases
        today = timezone.now().date()
        today_count = EyeDentalVoucher.objects.filter(created_at__date=today).count()

        return Response({
            'total': total,
            'today': today_count,
            'by_status': {item['status']: item['count'] for item in by_status},
            'by_service': {item['service_type']: item['count'] for item in by_service},
        })
