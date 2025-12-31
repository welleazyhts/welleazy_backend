from django.db import models
from apps.common.models import BaseModel
from apps.location.models import City
from apps.labtest.models import Test
from apps.labfilter.models import VisitType
from apps.consultation_filter.models import Vendor
from datetime import time


class DiagnosticCenter(BaseModel):
    """
    Represents a physical diagnostic center/lab location.
    Can be owned by a vendor (Apollo, Healthians) or be independent.
    Comprehensive model matching .NET app's InsertUpdateServiceProviderDetails().
    """
    DC_GRADE_CHOICES = [
        ('A', 'Grade A - Premium'),
        ('B', 'Grade B - Standard'),
        ('C', 'Grade C - Basic'),
    ]

    PROVIDER_TYPE_CHOICES = [
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('lab', 'Standalone Lab'),
        ('collection_center', 'Collection Center'),
        ('imaging_center', 'Imaging Center'),
    ]

    SPECIALTY_TYPE_CHOICES = [
        ('general', 'General'),
        ('multi_specialty', 'Multi-Specialty'),
        ('single_specialty', 'Single Specialty'),
        ('super_specialty', 'Super Specialty'),
    ]

    OWNERSHIP_CHOICES = [
        ('private', 'Private'),
        ('government', 'Government'),
        ('trust', 'Trust'),
        ('corporate', 'Corporate Chain'),
    ]

    PARTNERSHIP_TYPE_CHOICES = [
        ('empaneled', 'Empaneled'),
        ('partner', 'Partner'),
        ('franchise', 'Franchise'),
        ('owned', 'Owned'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
        ('blacklisted', 'Blacklisted'),
    ]

    # Basic Info
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, blank=True, null=True, unique=True)
    unique_name = models.CharField(max_length=255, blank=True, null=True, help_text="Short unique identifier")
    token_id = models.CharField(max_length=100, blank=True, null=True, help_text="Vendor registration token")

    # Classification
    provider_type = models.CharField(max_length=30, choices=PROVIDER_TYPE_CHOICES, default='lab')
    specialty_type = models.CharField(max_length=30, choices=SPECIALTY_TYPE_CHOICES, default='general')
    ownership = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default='private')
    partnership_type = models.CharField(max_length=20, choices=PARTNERSHIP_TYPE_CHOICES, default='empaneled')
    center_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=0, help_text="Higher = shown first")
    categorization = models.CharField(max_length=255, blank=True, null=True)

    # Corporate/Group Association
    corporate_group = models.CharField(max_length=255, blank=True, null=True, help_text="Parent group name")
    corporate_id = models.CharField(max_length=100, blank=True, null=True)

    # Vendor association
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diagnostic_centers",
        help_text="Vendor this DC belongs to (Apollo, Healthians, etc.)"
    )
    vendor_dc_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="DC ID in vendor's system for API calls"
    )

    # Location
    address = models.TextField(blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="diagnostic_centers")

    # Contact
    std_code = models.CharField(max_length=10, blank=True, null=True)
    landline_number = models.CharField(max_length=20, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    alternate_number = models.CharField(max_length=20, blank=True, null=True)
    fax_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)

    # Links
    google_address = models.TextField(blank=True, null=True)
    short_url = models.CharField(max_length=255, blank=True, null=True)
    location_link = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='dc_logos/', blank=True, null=True)

    # Operational Details
    active = models.BooleanField(default=True)
    grade = models.CharField(max_length=1, choices=DC_GRADE_CHOICES, default='B')
    work_start = models.TimeField(default=time(8, 0))
    work_end = models.TimeField(default=time(20, 0))
    sunday_open = models.BooleanField(default=False)

    # Slot Configuration
    slot_interval_minutes = models.IntegerField(default=30)
    slot_capacity = models.IntegerField(default=1)

    # Staff
    staff_strength = models.IntegerField(default=0)
    doctor_consultants = models.IntegerField(default=0)
    visiting_consultants = models.IntegerField(default=0)
    specialties_available = models.TextField(blank=True, null=True, help_text="Comma-separated specialties")

    # Services & Capabilities
    home_collection = models.BooleanField(default=False, help_text="Supports home sample collection")
    home_collection_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    home_delivery = models.BooleanField(default=False)
    delivery_tat = models.CharField(max_length=100, blank=True, null=True, help_text="Delivery turnaround time")
    service_area = models.TextField(blank=True, null=True, help_text="Areas served")
    service_pincodes = models.TextField(blank=True, null=True, help_text="Comma-separated pincodes served")
    visit_type = models.CharField(max_length=50, blank=True, null=True)
    has_parking = models.BooleanField(default=False)
    health_checkup = models.BooleanField(default=True)

    # Ambulance
    has_ambulance = models.BooleanField(default=False)
    bls_ambulance_count = models.IntegerField(default=0, help_text="Basic Life Support")
    acls_ambulance_count = models.IntegerField(default=0, help_text="Advanced Cardiac Life Support")

    # Accreditation
    is_nabl_accredited = models.BooleanField(default=False)
    is_cap_accredited = models.BooleanField(default=False)
    is_iso_certified = models.BooleanField(default=False)
    iso_type = models.CharField(max_length=50, blank=True, null=True)
    recognized_by = models.CharField(max_length=255, blank=True, null=True)
    accreditation_details = models.TextField(blank=True, null=True)

    # Banking Details
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_account_holder = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_branch = models.CharField(max_length=255, blank=True, null=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    payment_terms = models.IntegerField(default=30, help_text="Payment terms in days")

    # Legal/Tax
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)

    # Agreement
    mou_signed = models.BooleanField(default=False)
    mou_signed_date = models.DateField(blank=True, null=True)
    client_assign = models.TextField(blank=True, null=True, help_text="Assigned corporate clients")
    remarks = models.TextField(blank=True, null=True)

    # Deactivation
    deactivation_reason = models.TextField(blank=True, null=True)
    deactivation_date = models.DateField(blank=True, null=True)
    deactivated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_dcs'
    )

    # Services
    tests = models.ManyToManyField(Test, related_name="diagnostic_centers")
    visit_types = models.ManyToManyField(VisitType, related_name="diagnostic_centers", blank=True)
    health_packages = models.ManyToManyField(
        'health_packages.HealthPackage', related_name='diagnostic_centers', blank=True
    )
    sponsored_packages = models.ManyToManyField(
        'sponsored_packages.SponsoredPackage', related_name='diagnostic_centers', blank=True
    )

    class Meta:
        db_table = 'diagnostic_centers'
        ordering = ['name']

    def __str__(self):
        vendor_name = self.vendor.code if self.vendor else 'Independent'
        return f"{self.name} ({vendor_name})"


class DiagnosticCenterTest(BaseModel):
    """
    Links tests to DCs with specific pricing (may differ from vendor's default price).
    """
    diagnostic_center = models.ForeignKey(
        DiagnosticCenter,
        on_delete=models.CASCADE,
        related_name="dc_tests"
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="dc_tests")

    # Pricing at this DC
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Availability
    is_available = models.BooleanField(default=True)
    turnaround_hours = models.IntegerField(default=24, help_text="Report TAT in hours")

    class Meta:
        db_table = 'diagnostic_center_tests'
        unique_together = ['diagnostic_center', 'test']

    def __str__(self):
        return f"{self.diagnostic_center.name} - {self.test.name}"


class DCLaboratoryCapabilities(BaseModel):
    """
    Laboratory equipment and capabilities for a DC.
    Based on .NET app's InsertUpdateServiceProvider_LaboratoryDetails().
    """
    diagnostic_center = models.OneToOneField(
        DiagnosticCenter,
        on_delete=models.CASCADE,
        related_name='lab_capabilities'
    )

    # Lab Sections
    hematology = models.BooleanField(default=False)
    biochemistry = models.BooleanField(default=False)
    microbiology = models.BooleanField(default=False)
    pathology = models.BooleanField(default=False)
    serology = models.BooleanField(default=False)
    histopathology = models.BooleanField(default=False)
    endocrinology = models.BooleanField(default=False)
    cytology = models.BooleanField(default=False)
    immunology = models.BooleanField(default=False)

    # Imaging - Equipment Availability
    x_ray = models.BooleanField(default=False)
    digital_x_ray = models.BooleanField(default=False)
    ultra_sound = models.BooleanField(default=False)
    color_doppler = models.BooleanField(default=False)
    mammogram = models.BooleanField(default=False)
    ct_scan = models.BooleanField(default=False)
    mri = models.BooleanField(default=False)
    pet_scan = models.BooleanField(default=False)
    nuclear_imaging = models.BooleanField(default=False)

    # Cardiac
    ecg = models.BooleanField(default=False)
    pft = models.BooleanField(default=False, help_text="Pulmonary Function Test")
    tmt = models.BooleanField(default=False, help_text="Treadmill Test")
    echo_2d = models.BooleanField(default=False)
    fluoroscopy = models.BooleanField(default=False)

    # Equipment Count (if multiple)
    x_ray_count = models.IntegerField(default=0)
    ct_scan_count = models.IntegerField(default=0)
    mri_count = models.IntegerField(default=0)

    # Discount percentages for bulk
    x_ray_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ct_scan_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    mri_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'dc_laboratory_capabilities'

    def __str__(self):
        return f"{self.diagnostic_center.name} - Lab Capabilities"


class DCContact(BaseModel):
    """
    Key contact persons at a DC for different departments.
    """
    DEPARTMENT_CHOICES = [
        ('insurance_desk', 'Insurance Desk'),
        ('business_development', 'Business Development'),
        ('finance', 'Finance'),
        ('clinical_services', 'Clinical Services'),
        ('nursing_services', 'Nursing Services'),
        ('fund_transfer', 'Fund Transfer'),
        ('cashless_opd', 'Cashless OPD'),
        ('organization', 'Organization Head'),
        ('business_spoc', 'Business SPOC'),
        ('other', 'Other'),
    ]

    diagnostic_center = models.ForeignKey(
        DiagnosticCenter,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    department = models.CharField(max_length=30, choices=DEPARTMENT_CHOICES)
    title = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'dc_contacts'
        ordering = ['department', 'name']

    def __str__(self):
        return f"{self.diagnostic_center.name} - {self.get_department_display()} - {self.name}"


class DCDocument(BaseModel):
    """
    Documents uploaded for DC verification/compliance.
    Based on .NET app's InsertUpdateServiceProvider_DocumentsDetails().
    """
    DOCUMENT_TYPE_CHOICES = [
        ('registration_certificate', 'Registration Certificate'),
        ('bio_medical_waste_certificate', 'Bio Medical Waste Management Certificate'),
        ('building_permit', 'Building Permit'),
        ('fire_safety_license', 'Fire Safety License'),
        ('pndt_license', 'PNDT License'),
        ('radiation_protection_certificate', 'Radiation Protection Certificate'),
        ('pollution_noc', 'Pollution Control NOC'),
        ('nabh_nabl_certificate', 'NABH/NABL/ISO Certificate'),
        ('cancelled_cheque', 'Cancelled Cheque'),
        ('pan_card', 'PAN Card'),
        ('neft_declaration', 'NEFT Declaration Form'),
        ('gst_certificate', 'GST Certificate'),
        ('opd_tariff', 'OPD Tariff'),
        ('tpa_list', 'List of TPAs'),
        ('consultant_list', 'List of Consultants'),
        ('opd_schedule', 'OPD Schedule'),
        ('mou_copy', 'MOU Copy'),
        ('lol_legal', 'LOL Legal Document'),
        ('agreement', 'Agreement Document'),
        ('vendor_registration', 'Vendor Registration Form'),
        ('other', 'Other'),
    ]

    diagnostic_center = models.ForeignKey(
        DiagnosticCenter,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='dc_documents/')
    file_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_dc_documents'
    )
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'dc_documents'
        ordering = ['document_type', '-created_at']

    def __str__(self):
        return f"{self.diagnostic_center.name} - {self.get_document_type_display()}"
