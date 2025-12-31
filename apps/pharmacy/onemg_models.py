"""
Tata 1MG Integration Models

Models for tracking 1MG orders, webhooks, and synchronization status.
"""

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.pharmacy.models import PharmacyOrder


class OneMGOrder(BaseModel):
    """
    Tracks orders placed with Tata 1MG

    Links our PharmacyOrder to 1MG's order system.
    """

    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
        ('returned', 'Returned'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    # Link to our order
    pharmacy_order = models.OneToOneField(
        PharmacyOrder,
        on_delete=models.CASCADE,
        related_name='onemg_order'
    )

    # 1MG identifiers
    onemg_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    onemg_transaction_id = models.CharField(max_length=100, blank=True, null=True)

    # Order details from 1MG
    onemg_status = models.CharField(
        max_length=30,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    # Pricing from 1MG
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)

    # Dates
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)

    # Prescription
    prescription_verified = models.BooleanField(default=False)
    prescription_rejection_reason = models.TextField(blank=True, null=True)

    # Raw response storage for debugging
    last_api_response = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = '1MG Order'
        verbose_name_plural = '1MG Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"1MG Order {self.onemg_order_id} - {self.pharmacy_order.order_id}"


class OneMGOrderItem(BaseModel):
    """
    Individual items in a 1MG order with SKU mapping
    """

    onemg_order = models.ForeignKey(
        OneMGOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # 1MG SKU details
    sku_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)

    # Pricing
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Availability
    is_available = models.BooleanField(default=True)
    substituted_sku_id = models.CharField(max_length=100, blank=True, null=True)

    # Prescription requirement
    requires_prescription = models.BooleanField(default=False)

    class Meta:
        verbose_name = '1MG Order Item'
        verbose_name_plural = '1MG Order Items'

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class OneMGWebhookLog(BaseModel):
    """
    Log all webhook calls from 1MG for debugging and audit
    """

    EVENT_TYPES = (
        ('order_confirmed', 'Order Confirmed'),
        ('order_packed', 'Order Packed'),
        ('order_shipped', 'Order Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('order_stuck', 'Order Stuck'),
        ('prescription_rejected', 'Prescription Rejected'),
        ('payment_received', 'Payment Received'),
        ('refund_initiated', 'Refund Initiated'),
        ('unknown', 'Unknown'),
    )

    PROCESSING_STATUS = (
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    )

    # Webhook identification
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='unknown')

    # Related order
    onemg_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    pharmacy_order = models.ForeignKey(
        PharmacyOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onemg_webhooks'
    )

    # Request details
    request_headers = models.JSONField(blank=True, null=True)
    request_body = models.JSONField(blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    signature_valid = models.BooleanField(default=False)

    # Processing
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS,
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # IP tracking
    source_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = '1MG Webhook Log'
        verbose_name_plural = '1MG Webhook Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Webhook {self.event_id} - {self.event_type}"


class OneMGMedicineMapping(BaseModel):
    """
    Maps our Medicine model to 1MG SKU IDs

    This allows syncing between local medicine database and 1MG catalog.
    """

    medicine = models.OneToOneField(
        'pharmacy.Medicine',
        on_delete=models.CASCADE,
        related_name='onemg_mapping'
    )

    # 1MG identifiers
    sku_id = models.CharField(max_length=100, unique=True, db_index=True)
    onemg_name = models.CharField(max_length=255)

    # Deal IDs for promotions
    deal_ids = models.JSONField(blank=True, null=True)

    # Sync status
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active_on_onemg = models.BooleanField(default=True)

    # Price from 1MG
    onemg_mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    onemg_selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = '1MG Medicine Mapping'
        verbose_name_plural = '1MG Medicine Mappings'

    def __str__(self):
        return f"{self.medicine.name} -> {self.sku_id}"


class OneMGServiceableCity(BaseModel):
    """
    Cache of cities where 1MG delivery is available
    """

    city_name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = '1MG Serviceable City'
        verbose_name_plural = '1MG Serviceable Cities'
        ordering = ['city_name']

    def __str__(self):
        return self.city_name
