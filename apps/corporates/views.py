from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Count

from .models import (
    Corporate, CorporatePlan, CorporateEmployee,
    CorporateEmployeeDependant, CorporateBookingApproval, CorporateInvoice
)
from .serializers import (
    CorporateListSerializer, CorporateDetailSerializer, CorporateCreateSerializer,
    CorporatePlanSerializer,
    CorporateEmployeeListSerializer, CorporateEmployeeDetailSerializer, CorporateEmployeeCreateSerializer,
    CorporateEmployeeDependantSerializer,
    CorporateBookingApprovalSerializer,
    CorporateInvoiceListSerializer, CorporateInvoiceDetailSerializer
)


class CorporateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing corporate clients"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'city': ['exact'],
        'account_manager': ['exact'],
        'billing_cycle': ['exact'],
    }
    search_fields = ['name', 'code', 'contact_person', 'contact_email']
    ordering_fields = ['name', 'created_at', 'contract_end_date']
    ordering = ['name']

    def get_queryset(self):
        return Corporate.objects.select_related('city', 'account_manager').prefetch_related('plans', 'employees')

    def get_serializer_class(self):
        if self.action == 'list':
            return CorporateListSerializer
        elif self.action == 'create':
            return CorporateCreateSerializer
        return CorporateDetailSerializer

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees for a corporate"""
        corporate = self.get_object()
        employees = corporate.employees.all()

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            employees = employees.filter(status=status_filter)

        serializer = CorporateEmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def plans(self, request, pk=None):
        """Get all plans for a corporate"""
        corporate = self.get_object()
        plans = corporate.plans.all()
        serializer = CorporatePlanSerializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """Get all invoices for a corporate"""
        corporate = self.get_object()
        invoices = corporate.invoices.all().order_by('-invoice_date')
        serializer = CorporateInvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get usage statistics for a corporate"""
        corporate = self.get_object()
        employees = corporate.employees.filter(status='active')

        return Response({
            'total_employees': employees.count(),
            'total_consultations_used': employees.aggregate(
                total=Sum('consultations_used')
            )['total'] or 0,
            'total_diagnostic_used': employees.aggregate(
                total=Sum('diagnostic_amount_used')
            )['total'] or 0,
            'total_pharmacy_used': employees.aggregate(
                total=Sum('pharmacy_amount_used')
            )['total'] or 0,
            'total_cases': corporate.cases.count(),
            'pending_approvals': CorporateBookingApproval.objects.filter(
                employee__corporate=corporate,
                status='pending'
            ).count(),
        })


class CorporatePlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing corporate plans"""
    serializer_class = CorporatePlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['corporate', 'plan_type', 'is_active']

    def get_queryset(self):
        return CorporatePlan.objects.select_related('corporate')


class CorporateEmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing corporate employees"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'corporate': ['exact'],
        'status': ['exact', 'in'],
        'plan': ['exact', 'isnull'],
        'department': ['exact'],
    }
    search_fields = ['name', 'employee_id', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'date_of_joining']
    ordering = ['name']

    def get_queryset(self):
        return CorporateEmployee.objects.select_related(
            'corporate', 'plan', 'user', 'verified_by'
        ).prefetch_related('dependants')

    def get_serializer_class(self):
        if self.action == 'list':
            return CorporateEmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CorporateEmployeeCreateSerializer
        return CorporateEmployeeDetailSerializer

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify an employee"""
        employee = self.get_object()
        employee.status = 'active'
        employee.verified_at = timezone.now()
        employee.verified_by = request.user
        employee.save()
        return Response(CorporateEmployeeDetailSerializer(employee).data)

    @action(detail=True, methods=['post'])
    def add_dependant(self, request, pk=None):
        """Add a dependant to an employee"""
        employee = self.get_object()
        serializer = CorporateEmployeeDependantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dependant = CorporateEmployeeDependant.objects.create(
            employee=employee,
            **serializer.validated_data
        )

        return Response(
            CorporateEmployeeDependantSerializer(dependant).data,
            status=status.HTTP_201_CREATED
        )


class CorporateBookingApprovalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing booking approvals"""
    serializer_class = CorporateBookingApprovalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'employee__corporate': ['exact'],
        'approver': ['exact', 'isnull'],
    }
    ordering = ['-created_at']

    def get_queryset(self):
        return CorporateBookingApproval.objects.select_related(
            'case', 'employee', 'employee__corporate', 'approver'
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a booking request"""
        approval = self.get_object()
        approved_amount = request.data.get('approved_amount', approval.requested_amount)
        remarks = request.data.get('remarks', '')

        approval.status = 'approved'
        approval.approved_amount = approved_amount
        approval.approver = request.user
        approval.approved_at = timezone.now()
        approval.remarks = remarks
        approval.save()

        # Update the case status if needed
        if approval.case:
            approval.case.status = 'confirmed'
            approval.case.save()

        return Response(CorporateBookingApprovalSerializer(approval).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a booking request"""
        approval = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')

        approval.status = 'rejected'
        approval.approver = request.user
        approval.approved_at = timezone.now()
        approval.rejection_reason = rejection_reason
        approval.save()

        # Update the case status if needed
        if approval.case:
            approval.case.status = 'cancelled'
            approval.case.save()

        return Response(CorporateBookingApprovalSerializer(approval).data)


class CorporateInvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing corporate invoices"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'corporate': ['exact'],
        'status': ['exact', 'in'],
        'invoice_date': ['gte', 'lte'],
    }
    ordering = ['-invoice_date']

    def get_queryset(self):
        return CorporateInvoice.objects.select_related('corporate')

    def get_serializer_class(self):
        if self.action == 'list':
            return CorporateInvoiceListSerializer
        return CorporateInvoiceDetailSerializer

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark an invoice as paid"""
        invoice = self.get_object()
        paid_amount = request.data.get('paid_amount', invoice.total_amount)

        invoice.paid_amount = paid_amount
        invoice.paid_at = timezone.now()
        if paid_amount >= invoice.total_amount:
            invoice.status = 'paid'
        else:
            invoice.status = 'partial'
        invoice.save()

        return Response(CorporateInvoiceDetailSerializer(invoice).data)
