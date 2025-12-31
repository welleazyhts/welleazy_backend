from django.db import models
import uuid
from django.conf import settings
from apps.consultation_filter.models import Vendor
from apps.location.models import State, City

User = settings.AUTH_USER_MODEL


# ---------------------------------------
#  EYE/DENTAL SERVICES (Program Categories)
# ---------------------------------------
class EyeDentalService(models.Model):
    """
    Service programs for Eye Care and Dental Care.
    Maps to Tbl_EyeDentalServices in .NET app.
    """
    SERVICE_TYPE_CHOICES = [
        ("eye", "Eye Care"),
        ("dental", "Dental Care"),
    ]

    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    detailed_description = models.TextField(blank=True)
    image = models.ImageField(upload_to="eyedental_services/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "eye_dental_services"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.name}"


# ---------------------------------------
#  EYE TREATMENTS
# ---------------------------------------
class EyeTreatment(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    detailed_description = models.TextField(blank=True)
    image = models.ImageField(upload_to="eye_treatments/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "eye_treatments"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------
#  DENTAL TREATMENTS
# ---------------------------------------
class DentalTreatment(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    detailed_description = models.TextField(blank=True)
    image = models.ImageField(upload_to="dental_treatments/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "dental_treatments"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------
#  EYE VENDORS
# ---------------------------------------
class EyeVendorAddress(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="eye_addresses")
    name = models.CharField(max_length=255, blank=True, null=True, help_text="Center name (if different from vendor)")
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="eye_vendors")
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="eye_vendors")
    pincode = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    treatments = models.ManyToManyField(EyeTreatment, blank=True, related_name="vendors")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "eye_vendor_addresses"
        ordering = ["vendor__name"]

    def __str__(self):
        return f"{self.vendor.name} - {self.city.name if self.city else self.address[:30]}"


# ---------------------------------------
#  DENTAL VENDORS
# ---------------------------------------
class DentalVendorAddress(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="dental_addresses")
    name = models.CharField(max_length=255, blank=True, null=True, help_text="Center name (if different from vendor)")
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="dental_vendors")
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="dental_vendors")
    pincode = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    treatments = models.ManyToManyField(DentalTreatment, blank=True, related_name="vendors")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "dental_vendor_addresses"
        ordering = ["vendor__name"]

    def __str__(self):
        return f"{self.vendor.name} - {self.city.name if self.city else self.address[:30]}"




class EyeDentalVoucher(models.Model):
    """
    Eye/Dental Treatment Case/Voucher.
    Maps to Tbl_EyeDentalTreatmentCaseDetails in .NET app.
    """

    SERVICE_TYPE = [
        ("eye", "Eye Care"),
        ("dental", "Dental Care"),
    ]

    BOOKING_FOR = [
        ("self", "Self"),
        ("dependant", "Dependant"),
    ]

    STATUS_CHOICES = [
        ("fresh", "Fresh Case"),
        ("pending", "Pending"),
        ("in_process", "In Process"),
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_id = models.CharField(max_length=20, unique=True, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="eye_dental_vouchers")

    # Corporate/Branch info (for enterprise customers)
    corporate_id = models.IntegerField(null=True, blank=True)
    corporate_branch_id = models.IntegerField(null=True, blank=True)

    booking_for = models.CharField(max_length=20, choices=BOOKING_FOR, default="self")
    dependant_name = models.CharField(max_length=255, blank=True, null=True)
    dependant_relationship = models.CharField(max_length=255, blank=True, null=True)
    dependant_id = models.IntegerField(null=True, blank=True, help_text="EmployeeDependentDetailsId")

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="fresh")

    # Treatments
    eye_treatment = models.ForeignKey(EyeTreatment, null=True, blank=True, on_delete=models.SET_NULL, related_name="vouchers")
    dental_treatment = models.ForeignKey(DentalTreatment, null=True, blank=True, on_delete=models.SET_NULL, related_name="vouchers")

    # Vendors
    eye_vendor = models.ForeignKey(EyeVendorAddress, null=True, blank=True, on_delete=models.SET_NULL, related_name="vouchers")
    dental_vendor = models.ForeignKey(DentalVendorAddress, null=True, blank=True, on_delete=models.SET_NULL, related_name="vouchers")

    # Snapshot fields (stored values at time of booking for records)
    vendor_name_snapshot = models.CharField(max_length=255, blank=True, default="")
    vendor_address_snapshot = models.TextField(blank=True, default="")
    service_name_snapshot = models.CharField(max_length=255, blank=True, default="")
    treatment_name_snapshot = models.CharField(max_length=255, blank=True, default="")

    # Appointment details
    appointment_date = models.DateField(null=True, blank=True)
    appointment_time = models.TimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    # User / dependant details
    name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    state = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=255, blank=True, default="")
    address = models.TextField(blank=True, default="")

    # Admin remarks
    comment = models.TextField(blank=True, default="", help_text="Admin remarks/notes")
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="updated_eye_dental_vouchers",
        help_text="Last updated by admin user"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "eye_dental_vouchers"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.request_id:
            last_id = EyeDentalVoucher.objects.count() + 1
            self.request_id = f"WX{last_id:06d}"

        # Auto-populate snapshot fields on create
        if not self.pk:
            if self.service_type == "eye":
                if self.eye_vendor:
                    self.vendor_name_snapshot = self.eye_vendor.name or self.eye_vendor.vendor.name
                    self.vendor_address_snapshot = self.eye_vendor.address
                if self.eye_treatment:
                    self.treatment_name_snapshot = self.eye_treatment.name
                self.service_name_snapshot = "Eye Care"
            elif self.service_type == "dental":
                if self.dental_vendor:
                    self.vendor_name_snapshot = self.dental_vendor.name or self.dental_vendor.vendor.name
                    self.vendor_address_snapshot = self.dental_vendor.address
                if self.dental_treatment:
                    self.treatment_name_snapshot = self.dental_treatment.name
                self.service_name_snapshot = "Dental Care"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.request_id


# ---------------------------------------
#  VOUCHER REMARKS/HISTORY
# ---------------------------------------
class EyeDentalVoucherRemark(models.Model):
    """
    Remarks/notes history for voucher cases.
    Maps to Tbl_MiscellaneousCaseRemarks in .NET app.
    """
    voucher = models.ForeignKey(EyeDentalVoucher, on_delete=models.CASCADE, related_name="remarks")
    remark = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "eye_dental_voucher_remarks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Remark for {self.voucher.request_id}"


