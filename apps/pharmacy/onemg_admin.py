"""
Tata 1MG Admin Configuration

Admin interface for managing 1MG integration data.
"""

from django.contrib import admin
from apps.pharmacy.onemg_models import (
    OneMGOrder,
    OneMGOrderItem,
    OneMGWebhookLog,
    OneMGMedicineMapping,
    OneMGServiceableCity,
)


class OneMGOrderItemInline(admin.TabularInline):
    model = OneMGOrderItem
    extra = 0
    readonly_fields = ['sku_id', 'product_name', 'quantity', 'selling_price', 'total']


@admin.register(OneMGOrder)
class OneMGOrderAdmin(admin.ModelAdmin):
    list_display = [
        'onemg_order_id',
        'pharmacy_order',
        'onemg_status',
        'payment_status',
        'total_amount',
        'created_at',
    ]
    list_filter = ['onemg_status', 'payment_status', 'created_at']
    search_fields = ['onemg_order_id', 'pharmacy_order__order_id']
    readonly_fields = [
        'onemg_order_id',
        'onemg_transaction_id',
        'last_api_response',
        'created_at',
        'updated_at',
    ]
    inlines = [OneMGOrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('pharmacy_order', 'onemg_order_id', 'onemg_transaction_id')
        }),
        ('Status', {
            'fields': ('onemg_status', 'payment_status', 'prescription_verified')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'discount', 'delivery_charge', 'total_amount')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'tracking_url', 'courier_name')
        }),
        ('Dates', {
            'fields': (
                'estimated_delivery_date',
                'shipped_at',
                'actual_delivery_date',
                'created_at',
                'updated_at',
            )
        }),
        ('Debug', {
            'fields': ('last_api_response', 'prescription_rejection_reason'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OneMGWebhookLog)
class OneMGWebhookLogAdmin(admin.ModelAdmin):
    list_display = [
        'event_id',
        'event_type',
        'onemg_order_id',
        'processing_status',
        'signature_valid',
        'created_at',
    ]
    list_filter = ['event_type', 'processing_status', 'signature_valid', 'created_at']
    search_fields = ['event_id', 'onemg_order_id']
    readonly_fields = [
        'event_id',
        'event_type',
        'onemg_order_id',
        'request_headers',
        'request_body',
        'signature',
        'signature_valid',
        'source_ip',
        'created_at',
    ]

    fieldsets = (
        ('Event', {
            'fields': ('event_id', 'event_type', 'onemg_order_id', 'pharmacy_order')
        }),
        ('Request', {
            'fields': ('request_headers', 'request_body', 'signature', 'signature_valid', 'source_ip')
        }),
        ('Processing', {
            'fields': ('processing_status', 'error_message', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(OneMGMedicineMapping)
class OneMGMedicineMappingAdmin(admin.ModelAdmin):
    list_display = [
        'medicine',
        'sku_id',
        'onemg_name',
        'onemg_selling_price',
        'is_active_on_onemg',
        'last_synced_at',
    ]
    list_filter = ['is_active_on_onemg', 'last_synced_at']
    search_fields = ['medicine__name', 'sku_id', 'onemg_name']
    raw_id_fields = ['medicine']


@admin.register(OneMGServiceableCity)
class OneMGServiceableCityAdmin(admin.ModelAdmin):
    list_display = ['city_name', 'state', 'is_active']
    list_filter = ['is_active', 'state']
    search_fields = ['city_name', 'state']
