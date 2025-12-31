"""
Provider-related models for storing configurations and tracking external appointments.
"""

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class ProviderConfiguration(BaseModel):
    """
    Stores provider API configurations.
    Allows dynamic configuration without code changes.
    """

    PROVIDER_TYPES = [
        ('consultation', 'Consultation'),
        ('diagnostics', 'Diagnostics'),
        ('pharmacy', 'Pharmacy'),
    ]

    name = models.CharField(max_length=50, help_text="Provider identifier e.g., 'apollo', 'onemg'")
    display_name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)

    # API Configuration (stored as JSON)
    api_base_url = models.URLField(blank=True)
    api_credentials = models.JSONField(
        default=dict,
        blank=True,
        help_text="Encrypted credentials like api_key, username, password"
    )
    additional_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional configuration like agreement_id, client_id"
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Capabilities
    supports_tele_consultation = models.BooleanField(default=False)
    supports_video_consultation = models.BooleanField(default=False)
    supports_in_clinic = models.BooleanField(default=False)
    supports_home_collection = models.BooleanField(default=False)
    supports_walk_in = models.BooleanField(default=False)

    class Meta:
        unique_together = ['name', 'provider_type']
        ordering = ['provider_type', 'name']

    def __str__(self):
        return f"{self.display_name} ({self.provider_type})"

    def get_full_config(self) -> dict:
        """Get complete configuration dict for provider initialization."""
        config = {
            'api_base_url': self.api_base_url,
            **self.api_credentials,
            **self.additional_config,
        }
        return config


class ExternalAppointment(BaseModel):
    """
    Tracks appointments made through external providers.
    Links to local Appointment model while storing provider-specific data.
    """

    APPOINTMENT_TYPES = [
        ('consultation', 'Consultation'),
        ('diagnostic', 'Diagnostic'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]

    # User & Local Reference
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='external_appointments'
    )
    local_appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='external_reference'
    )

    # Provider Information
    provider_name = models.CharField(max_length=50)  # e.g., 'apollo', 'thyrocare'
    provider_appointment_id = models.CharField(max_length=100)
    provider_booking_id = models.CharField(max_length=100, blank=True)
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)

    # Appointment Details
    doctor_id = models.CharField(max_length=100, blank=True)
    doctor_name = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    hospital_id = models.CharField(max_length=100, blank=True)
    hospital_name = models.CharField(max_length=200, blank=True)

    # Schedule
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    consultation_type = models.CharField(max_length=20, blank=True)  # tele/video/in_clinic

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_updated_at = models.DateTimeField(auto_now=True)

    # Fees
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Additional Data
    meeting_link = models.URLField(blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['provider_name', 'provider_appointment_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['appointment_date']),
        ]

    def __str__(self):
        return f"{self.provider_name} - {self.doctor_name} on {self.appointment_date}"


class ExternalLabBooking(BaseModel):
    """
    Tracks lab/diagnostic bookings made through external providers.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('report_ready', 'Report Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    COLLECTION_TYPES = [
        ('home_collection', 'Home Collection'),
        ('walk_in', 'Walk-in'),
    ]

    # User & Reference
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='external_lab_bookings'
    )

    # Provider Information
    provider_name = models.CharField(max_length=50)
    provider_booking_id = models.CharField(max_length=100)
    provider_order_id = models.CharField(max_length=100, blank=True)

    # Patient Details
    patient_name = models.CharField(max_length=200)
    patient_mobile = models.CharField(max_length=15)
    patient_email = models.EmailField(blank=True)

    # Booking Details
    collection_type = models.CharField(max_length=20, choices=COLLECTION_TYPES)
    center_id = models.CharField(max_length=100, blank=True)
    center_name = models.CharField(max_length=200, blank=True)

    # Address (for home collection)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    # Schedule
    booking_date = models.DateField()
    slot_time = models.TimeField(null=True, blank=True)

    # Tests/Packages
    tests = models.JSONField(default=list)  # List of test IDs and names
    packages = models.JSONField(default=list)  # List of package IDs and names

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_updated_at = models.DateTimeField(auto_now=True)

    # Phlebotomist (for home collection)
    phlebotomist_name = models.CharField(max_length=200, blank=True)
    phlebotomist_phone = models.CharField(max_length=15, blank=True)

    # Fees
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Reports
    reports_available = models.BooleanField(default=False)
    report_urls = models.JSONField(default=list)

    # Additional Data
    provider_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-booking_date', '-created_at']
        indexes = [
            models.Index(fields=['provider_name', 'provider_booking_id']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.provider_name} - {self.patient_name} on {self.booking_date}"


class ProviderWebhookLog(BaseModel):
    """
    Logs all webhook calls from providers for debugging and audit.
    """

    provider_name = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    reference_id = models.CharField(max_length=100, blank=True)

    # Request Data
    headers = models.JSONField(default=dict)
    payload = models.JSONField(default=dict)

    # Processing
    processed = models.BooleanField(default=False)
    processing_result = models.TextField(blank=True)
    processing_error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider_name', 'event_type']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.provider_name} - {self.event_type} at {self.created_at}"
