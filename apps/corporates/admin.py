from django.contrib import admin
from .models import (
    Corporate, CorporatePlan, CorporateEmployee,
    CorporateEmployeeDependant, CorporateBookingApproval, CorporateInvoice
)


class CorporatePlanInline(admin.TabularInline):
    model = CorporatePlan
    extra = 0


class CorporateEmployeeInline(admin.TabularInline):
    model = CorporateEmployee
    extra = 0
    fields = ['employee_id', 'name', 'email', 'department', 'status', 'plan']


@admin.register(Corporate)
class CorporateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'status', 'employee_count',
        'contact_person', 'city', 'account_manager'
    ]
    list_filter = ['status', 'city', 'billing_cycle']
    search_fields = ['name', 'code', 'contact_email', 'contact_phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CorporatePlanInline]
    filter_horizontal = ['preferred_vendors']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'code', 'logo', 'industry', 'employee_count', 'status')
        }),
        ('Contact Details', {
            'fields': (
                'contact_person', 'contact_email', 'contact_phone',
                'hr_email', 'hr_phone'
            )
        }),
        ('Business Details', {
            'fields': ('gst_number', 'pan_number', 'cin_number', 'billing_address')
        }),
        ('Location', {
            'fields': ('city', 'address', 'pincode')
        }),
        ('Contract', {
            'fields': (
                'contract_start_date', 'contract_end_date',
                'contract_value', 'billing_cycle'
            )
        }),
        ('Settings', {
            'fields': (
                'is_self_registration', 'requires_approval',
                'preferred_vendors', 'account_manager', 'extra_config'
            )
        }),
    )


@admin.register(CorporatePlan)
class CorporatePlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'corporate', 'plan_type', 'is_active',
        'per_employee_cost', 'consultation_limit'
    ]
    list_filter = ['plan_type', 'is_active', 'covers_spouse', 'covers_children']
    search_fields = ['name', 'corporate__name']
    filter_horizontal = ['tests', 'health_packages']

    fieldsets = (
        ('Basic', {
            'fields': ('corporate', 'name', 'description', 'plan_type', 'is_active')
        }),
        ('Coverage', {
            'fields': (
                'covers_employee', 'covers_spouse',
                'covers_children', 'covers_parents', 'max_dependants'
            )
        }),
        ('Services', {
            'fields': ('tests', 'health_packages')
        }),
        ('Limits', {
            'fields': ('consultation_limit', 'diagnostic_limit', 'pharmacy_limit')
        }),
        ('Pricing', {
            'fields': ('per_employee_cost', 'per_dependant_cost')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
    )


class CorporateEmployeeDependantInline(admin.TabularInline):
    model = CorporateEmployeeDependant
    extra = 0


@admin.register(CorporateEmployee)
class CorporateEmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'employee_id', 'corporate', 'email',
        'department', 'status', 'plan'
    ]
    list_filter = ['status', 'corporate', 'department']
    search_fields = ['name', 'employee_id', 'email', 'phone']
    readonly_fields = ['verified_at', 'verified_by']
    inlines = [CorporateEmployeeDependantInline]

    fieldsets = (
        ('Employee Info', {
            'fields': (
                'corporate', 'user', 'employee_id', 'name',
                'email', 'phone', 'department', 'designation', 'date_of_joining'
            )
        }),
        ('Plan', {
            'fields': ('plan', 'status')
        }),
        ('Verification', {
            'fields': ('verified_at', 'verified_by'),
            'classes': ('collapse',)
        }),
        ('Usage', {
            'fields': (
                'consultations_used', 'diagnostic_amount_used', 'pharmacy_amount_used'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(CorporateEmployeeDependant)
class CorporateEmployeeDependantAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee', 'relation', 'is_active']
    list_filter = ['relation', 'is_active']
    search_fields = ['name', 'employee__name', 'employee__employee_id']


@admin.register(CorporateBookingApproval)
class CorporateBookingApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'case', 'employee', 'status', 'requested_amount',
        'approved_amount', 'approver', 'approved_at'
    ]
    list_filter = ['status']
    search_fields = ['case__case_id', 'employee__name', 'employee__employee_id']
    readonly_fields = ['approved_at']


@admin.register(CorporateInvoice)
class CorporateInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'corporate', 'invoice_date',
        'total_amount', 'status', 'paid_amount'
    ]
    list_filter = ['status']
    search_fields = ['invoice_number', 'corporate__name']
    readonly_fields = ['paid_at']
    date_hierarchy = 'invoice_date'
