from django.db import models
from apps.common.models import BaseModel
# from django.contrib.auth.models import User
from django.conf import settings
from apps.location.models import City
from django.core.validators import RegexValidator


# Create your models here.


# DOCTOR SPECIALIZATIONS-----
class DoctorSpeciality(BaseModel):
    name=models.CharField(max_length=255,unique=True)
    description=models.TextField(blank=True, null=True)
    image=models.ImageField(upload_to='doctor_specializations/images/', blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
       db_table="doctor_specializations"
       ordering=["name"]

    def __str__(self):
        return self.name


# LANGUAGE SELECTION----

class Language(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # like 'en', 'hi', 'mr'
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table="languages"
        ordering=["name"]

    def __str__(self):
        return self.name


class UserLanguagePreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='language_preference')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} → {self.language}"


    # PINCODES---

class Pincode(BaseModel):
    code = models.CharField(max_length=6, unique=True, validators=[RegexValidator(r'^\d{6}$', 'Enter a valid 6-digit pincode')])
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="pincodes")
   


    class Meta:
        db_table="pincodes"

    def __str__(self):
        return f"{self.code} - {self.city.name}"
    
   



    # VENDOR LIST---

class Vendor(BaseModel):
    """
    Vendor represents external service providers like Apollo, Healthians, Lal PathLab, etc.
    Each vendor can provide multiple services: diagnostics, pharmacy, consultations, etc.
    """
    VENDOR_TYPE_CHOICES = [
        ('diagnostic', 'Diagnostic Lab'),
        ('pharmacy', 'Pharmacy'),
        ('consultation', 'Consultation'),
        ('gym', 'Gym/Fitness'),
        ('eyedental', 'Eye & Dental'),
        ('multi', 'Multi-Service'),
    ]

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True, help_text="Unique vendor code e.g., APOLLO, HEALTHIANS")
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPE_CHOICES, default='diagnostic')
    available = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    external_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    specialization = models.ForeignKey(DoctorSpeciality, on_delete=models.CASCADE, null=True, blank=True)

    # Contact Information
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Business Information
    business_address = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)

    # Service Coverage
    cities_served = models.ManyToManyField(City, related_name='vendors', blank=True)
    is_pan_india = models.BooleanField(default=False, help_text="Serves all cities")

    # Capabilities
    home_collection = models.BooleanField(default=False, help_text="Supports home sample collection")
    e_consultation = models.BooleanField(default=False, help_text="Supports e-consultation")
    in_clinic = models.BooleanField(default=False, help_text="Supports in-clinic visits")

    # Priority & Ranking
    priority = models.IntegerField(default=0, help_text="Higher priority vendors shown first")

    class Meta:
        db_table = 'vendors'
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class VendorAPIConfig(BaseModel):
    """
    Stores API credentials and configuration for external vendor integrations.
    """
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='api_config')

    # API Credentials
    api_base_url = models.URLField(help_text="Base URL for vendor API")
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    auth_token = models.TextField(blank=True, null=True, help_text="OAuth token if applicable")

    # Additional Config (JSON)
    extra_config = models.JSONField(default=dict, blank=True, help_text="Additional vendor-specific configuration")

    # Webhook URLs
    webhook_url = models.URLField(blank=True, null=True, help_text="Webhook URL for vendor callbacks")

    # Status
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'vendor_api_configs'

    def __str__(self):
        return f"API Config: {self.vendor.name}"


class VendorServiceMapping(BaseModel):
    """
    Maps vendor services to internal service types with pricing.
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='service_mappings')

    SERVICE_TYPE_CHOICES = [
        ('test', 'Lab Test'),
        ('package', 'Health Package'),
        ('consultation', 'Doctor Consultation'),
        ('pharmacy', 'Pharmacy Order'),
        ('home_visit', 'Home Visit Charges'),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    internal_service_id = models.CharField(max_length=100, help_text="Internal test/package/doctor ID")
    vendor_service_id = models.CharField(max_length=100, help_text="Vendor's service ID")
    vendor_service_name = models.CharField(max_length=255)

    # Pricing
    vendor_price = models.DecimalField(max_digits=10, decimal_places=2)
    our_price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vendor_service_mappings'
        unique_together = ['vendor', 'service_type', 'internal_service_id']

    def __str__(self):
        return f"{self.vendor.name} - {self.vendor_service_name}"




