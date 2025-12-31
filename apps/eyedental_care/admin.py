from django.contrib import admin
from .models import (
    EyeDentalService,
    EyeTreatment, DentalTreatment,
    EyeVendorAddress, DentalVendorAddress,
    EyeDentalVoucher, EyeDentalVoucherRemark
)


@admin.register(EyeDentalService)
class EyeDentalServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'service_type', 'display_order', 'is_active', 'created_at']
    list_filter = ['service_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'name']


@admin.register(EyeTreatment)
class EyeTreatmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'short_description']
    list_editable = ['is_active']


@admin.register(DentalTreatment)
class DentalTreatmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'short_description']
    list_editable = ['is_active']


@admin.register(EyeVendorAddress)
class EyeVendorAddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'vendor', 'name', 'city', 'consultation_fee', 'is_active']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['vendor__name', 'name', 'address']
    list_editable = ['is_active']
    filter_horizontal = ['treatments']
    raw_id_fields = ['vendor', 'city', 'state']


@admin.register(DentalVendorAddress)
class DentalVendorAddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'vendor', 'name', 'city', 'consultation_fee', 'is_active']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['vendor__name', 'name', 'address']
    list_editable = ['is_active']
    filter_horizontal = ['treatments']
    raw_id_fields = ['vendor', 'city', 'state']


class EyeDentalVoucherRemarkInline(admin.TabularInline):
    model = EyeDentalVoucherRemark
    extra = 1
    readonly_fields = ['created_by', 'created_at']


@admin.register(EyeDentalVoucher)
class EyeDentalVoucherAdmin(admin.ModelAdmin):
    list_display = [
        'request_id', 'user', 'service_type', 'status', 'booking_for',
        'name', 'treatment_name_snapshot', 'vendor_name_snapshot', 'created_at'
    ]
    list_filter = ['service_type', 'status', 'booking_for', 'created_at']
    search_fields = ['request_id', 'user__email', 'name', 'contact_number', 'vendor_name_snapshot']
    readonly_fields = ['request_id', 'created_at', 'updated_at', 'vendor_name_snapshot', 'vendor_address_snapshot',
                       'service_name_snapshot', 'treatment_name_snapshot']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'eye_treatment', 'dental_treatment', 'eye_vendor', 'dental_vendor', 'updated_by']
    inlines = [EyeDentalVoucherRemarkInline]
    fieldsets = (
        ('Voucher Info', {
            'fields': ('request_id', 'user', 'status', 'service_type')
        }),
        ('Corporate Info', {
            'fields': ('corporate_id', 'corporate_branch_id'),
            'classes': ('collapse',)
        }),
        ('Booking Details', {
            'fields': ('booking_for', 'dependant_name', 'dependant_relationship', 'dependant_id')
        }),
        ('Eye Care', {
            'fields': ('eye_treatment', 'eye_vendor'),
            'classes': ('collapse',)
        }),
        ('Dental Care', {
            'fields': ('dental_treatment', 'dental_vendor'),
            'classes': ('collapse',)
        }),
        ('Snapshot Data (Read Only)', {
            'fields': ('vendor_name_snapshot', 'vendor_address_snapshot', 'service_name_snapshot', 'treatment_name_snapshot'),
            'classes': ('collapse',)
        }),
        ('Appointment', {
            'fields': ('appointment_date', 'appointment_time', 'activated_at')
        }),
        ('Contact Info', {
            'fields': ('name', 'contact_number', 'email', 'state', 'city', 'address')
        }),
        ('Admin Notes', {
            'fields': ('comment', 'updated_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EyeDentalVoucherRemark)
class EyeDentalVoucherRemarkAdmin(admin.ModelAdmin):
    list_display = ['id', 'voucher', 'remark', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['voucher__request_id', 'remark']
    raw_id_fields = ['voucher', 'created_by']
