from rest_framework import serializers
from .models import (
    Corporate, CorporatePlan, CorporateEmployee,
    CorporateEmployeeDependant, CorporateBookingApproval, CorporateInvoice
)


class CorporateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    city_name = serializers.CharField(source='city.name', read_only=True)
    account_manager_name = serializers.CharField(source='account_manager.full_name', read_only=True)
    active_employees = serializers.SerializerMethodField()

    class Meta:
        model = Corporate
        fields = [
            'id', 'name', 'code', 'status', 'employee_count',
            'contact_person', 'contact_email', 'contact_phone',
            'city_name', 'account_manager_name', 'active_employees',
            'contract_start_date', 'contract_end_date'
        ]

    def get_active_employees(self, obj):
        return obj.employees.filter(status='active').count()


class CorporatePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporatePlan
        fields = [
            'id', 'name', 'description', 'plan_type',
            'covers_employee', 'covers_spouse', 'covers_children', 'covers_parents',
            'max_dependants', 'consultation_limit', 'diagnostic_limit', 'pharmacy_limit',
            'per_employee_cost', 'per_dependant_cost',
            'is_active', 'valid_from', 'valid_until'
        ]


class CorporateDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views"""
    city_name = serializers.CharField(source='city.name', read_only=True)
    account_manager_name = serializers.CharField(source='account_manager.full_name', read_only=True)
    plans = CorporatePlanSerializer(many=True, read_only=True)
    preferred_vendor_names = serializers.SerializerMethodField()
    employee_stats = serializers.SerializerMethodField()

    class Meta:
        model = Corporate
        fields = [
            'id', 'name', 'code', 'logo', 'industry', 'employee_count', 'status',
            'contact_person', 'contact_email', 'contact_phone', 'hr_email', 'hr_phone',
            'gst_number', 'pan_number', 'cin_number', 'billing_address',
            'city', 'city_name', 'address', 'pincode',
            'contract_start_date', 'contract_end_date', 'contract_value', 'billing_cycle',
            'is_self_registration', 'requires_approval',
            'preferred_vendors', 'preferred_vendor_names',
            'account_manager', 'account_manager_name',
            'extra_config', 'plans', 'employee_stats',
            'created_at', 'updated_at'
        ]

    def get_preferred_vendor_names(self, obj):
        return list(obj.preferred_vendors.values_list('name', flat=True))

    def get_employee_stats(self, obj):
        employees = obj.employees.all()
        return {
            'total': employees.count(),
            'active': employees.filter(status='active').count(),
            'pending': employees.filter(status='pending').count(),
            'inactive': employees.filter(status='inactive').count(),
        }


class CorporateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating corporates"""
    class Meta:
        model = Corporate
        fields = [
            'name', 'code', 'logo', 'industry', 'employee_count', 'status',
            'contact_person', 'contact_email', 'contact_phone', 'hr_email', 'hr_phone',
            'gst_number', 'pan_number', 'cin_number', 'billing_address',
            'city', 'address', 'pincode',
            'contract_start_date', 'contract_end_date', 'contract_value', 'billing_cycle',
            'is_self_registration', 'requires_approval',
            'preferred_vendors', 'account_manager', 'extra_config'
        ]


class CorporateEmployeeDependantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateEmployeeDependant
        fields = ['id', 'name', 'relation', 'date_of_birth', 'gender', 'is_active']


class CorporateEmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    corporate_name = serializers.CharField(source='corporate.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = CorporateEmployee
        fields = [
            'id', 'corporate', 'corporate_name', 'employee_id', 'name',
            'email', 'phone', 'department', 'designation', 'status',
            'plan', 'plan_name', 'consultations_used',
            'diagnostic_amount_used', 'pharmacy_amount_used'
        ]


class CorporateEmployeeDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested data"""
    corporate_name = serializers.CharField(source='corporate.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    dependants = CorporateEmployeeDependantSerializer(many=True, read_only=True)
    consultation_remaining = serializers.ReadOnlyField()
    diagnostic_remaining = serializers.ReadOnlyField()

    class Meta:
        model = CorporateEmployee
        fields = [
            'id', 'corporate', 'corporate_name', 'user',
            'employee_id', 'name', 'email', 'phone',
            'department', 'designation', 'date_of_joining',
            'plan', 'plan_name', 'status',
            'verified_at', 'verified_by',
            'consultations_used', 'diagnostic_amount_used', 'pharmacy_amount_used',
            'consultation_remaining', 'diagnostic_remaining',
            'dependants', 'created_at', 'updated_at'
        ]


class CorporateEmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    class Meta:
        model = CorporateEmployee
        fields = [
            'corporate', 'user', 'employee_id', 'name', 'email', 'phone',
            'department', 'designation', 'date_of_joining', 'plan', 'status'
        ]


class CorporateBookingApprovalSerializer(serializers.ModelSerializer):
    case_id = serializers.CharField(source='case.case_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    approver_name = serializers.CharField(source='approver.full_name', read_only=True)

    class Meta:
        model = CorporateBookingApproval
        fields = [
            'id', 'case', 'case_id', 'employee', 'employee_name',
            'status', 'requested_amount', 'approved_amount',
            'approver', 'approver_name', 'approved_at',
            'rejection_reason', 'remarks', 'created_at'
        ]


class CorporateInvoiceListSerializer(serializers.ModelSerializer):
    corporate_name = serializers.CharField(source='corporate.name', read_only=True)

    class Meta:
        model = CorporateInvoice
        fields = [
            'id', 'invoice_number', 'corporate', 'corporate_name',
            'invoice_date', 'due_date', 'period_start', 'period_end',
            'total_amount', 'status', 'paid_amount'
        ]


class CorporateInvoiceDetailSerializer(serializers.ModelSerializer):
    corporate_name = serializers.CharField(source='corporate.name', read_only=True)

    class Meta:
        model = CorporateInvoice
        fields = [
            'id', 'invoice_number', 'corporate', 'corporate_name',
            'invoice_date', 'due_date', 'period_start', 'period_end',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'status', 'paid_amount', 'paid_at', 'invoice_file', 'notes',
            'created_at', 'updated_at'
        ]
