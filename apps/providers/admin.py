from django.contrib import admin
from .models import (
    ProviderConfiguration,
    ExternalAppointment,
    ExternalLabBooking,
    ProviderWebhookLog,
)


@admin.register(ProviderConfiguration)
class ProviderConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'provider_type', 'is_active', 'is_default']
    list_filter = ['provider_type', 'is_active', 'is_default']
    search_fields = ['name', 'display_name']
    list_editable = ['is_active', 'is_default']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'provider_type')
        }),
        ('API Configuration', {
            'fields': ('api_base_url', 'api_credentials', 'additional_config'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
        ('Capabilities', {
            'fields': (
                'supports_tele_consultation',
                'supports_video_consultation',
                'supports_in_clinic',
                'supports_home_collection',
                'supports_walk_in',
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExternalAppointment)
class ExternalAppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'provider_name', 'doctor_name',
        'appointment_date', 'appointment_time', 'status'
    ]
    list_filter = ['provider_name', 'status', 'appointment_type', 'consultation_type']
    search_fields = ['user__email', 'doctor_name', 'provider_appointment_id']
    date_hierarchy = 'appointment_date'
    readonly_fields = [
        'provider_appointment_id', 'provider_booking_id',
        'provider_response', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('User & Reference', {
            'fields': ('user', 'local_appointment')
        }),
        ('Provider Info', {
            'fields': (
                'provider_name', 'provider_appointment_id',
                'provider_booking_id', 'appointment_type'
            )
        }),
        ('Doctor & Hospital', {
            'fields': (
                'doctor_id', 'doctor_name', 'specialization',
                'hospital_id', 'hospital_name'
            )
        }),
        ('Schedule', {
            'fields': ('appointment_date', 'appointment_time', 'consultation_type')
        }),
        ('Status & Fees', {
            'fields': (
                'status', 'consultation_fee', 'discount_amount',
                'final_amount', 'meeting_link'
            )
        }),
        ('Additional Data', {
            'fields': ('provider_response', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExternalLabBooking)
class ExternalLabBookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'provider_name', 'patient_name',
        'booking_date', 'collection_type', 'status'
    ]
    list_filter = ['provider_name', 'status', 'collection_type']
    search_fields = ['user__email', 'patient_name', 'provider_booking_id']
    date_hierarchy = 'booking_date'
    readonly_fields = ['provider_booking_id', 'provider_order_id', 'created_at', 'updated_at']


@admin.register(ProviderWebhookLog)
class ProviderWebhookLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider_name', 'event_type', 'reference_id', 'processed', 'created_at']
    list_filter = ['provider_name', 'event_type', 'processed']
    search_fields = ['reference_id', 'event_type']
    date_hierarchy = 'created_at'
    readonly_fields = ['headers', 'payload', 'created_at']
