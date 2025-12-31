from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.location.models import City
from apps.consultation_filter.models import Vendor
from apps.labtest.models import Test
from apps.health_packages.models import HealthPackage

User = settings.AUTH_USER_MODEL


class Corporate(BaseModel):
    """
    Corporate/Employer entity for B2B wellness programs.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
    ]

    # Basic Info
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, help_text="Unique corporate code")
    logo = models.ImageField(upload_to='corporates/logos/', blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    employee_count = models.PositiveIntegerField(default=0)

    # Contact Details
    contact_person = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    hr_email = models.EmailField(blank=True, null=True)
    hr_phone = models.CharField(max_length=20, blank=True, null=True)

    # Business Details
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    cin_number = models.CharField(max_length=30, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)

    # Location
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    # Contract Details
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    contract_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('half_yearly', 'Half Yearly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )

    # Status & Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_self_registration = models.BooleanField(
        default=False,
        help_text="Allow employees to self-register"
    )
    requires_approval = models.BooleanField(
        default=True,
        help_text="Require HR approval for bookings"
    )

    # Service Configuration
    preferred_vendors = models.ManyToManyField(
        Vendor,
        related_name='corporate_clients',
        blank=True,
        help_text="Preferred vendors for this corporate"
    )

    # Account Manager
    account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_corporates',
        help_text="Welleazy account manager for this corporate"
    )

    # Config
    extra_config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'corporates'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class CorporatePlan(BaseModel):
    """
    Wellness plans offered to corporate employees.
    """
    corporate = models.ForeignKey(Corporate, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    PLAN_TYPE_CHOICES = [
        ('basic', 'Basic Health Checkup'),
        ('standard', 'Standard Wellness'),
        ('premium', 'Premium Wellness'),
        ('executive', 'Executive Health'),
        ('custom', 'Custom Plan'),
    ]

    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='standard')

    # Coverage
    covers_employee = models.BooleanField(default=True)
    covers_spouse = models.BooleanField(default=False)
    covers_children = models.BooleanField(default=False)
    covers_parents = models.BooleanField(default=False)
    max_dependants = models.PositiveIntegerField(default=0)

    # Services Included
    tests = models.ManyToManyField(Test, related_name='corporate_plans', blank=True)
    health_packages = models.ManyToManyField(
        HealthPackage,
        related_name='corporate_plans',
        blank=True
    )

    # Limits
    consultation_limit = models.PositiveIntegerField(
        default=0,
        help_text="Number of consultations per year (0 = unlimited)"
    )
    diagnostic_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Annual diagnostic limit in INR (0 = unlimited)"
    )
    pharmacy_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Annual pharmacy limit in INR (0 = unlimited)"
    )

    # Pricing
    per_employee_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_dependant_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'corporate_plans'

    def __str__(self):
        return f"{self.corporate.name} - {self.name}"


class CorporateEmployee(BaseModel):
    """
    Employees registered under a corporate.
    Links corporate to user accounts.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Verification'),
        ('terminated', 'Terminated'),
    ]

    corporate = models.ForeignKey(Corporate, on_delete=models.CASCADE, related_name='employees')
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corporate_memberships'
    )

    # Employee Info
    employee_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    date_of_joining = models.DateField(null=True, blank=True)

    # Plan Assignment
    plan = models.ForeignKey(
        CorporatePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrolled_employees'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_employees'
    )

    # Usage Tracking
    consultations_used = models.PositiveIntegerField(default=0)
    diagnostic_amount_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pharmacy_amount_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'corporate_employees'
        unique_together = ['corporate', 'employee_id']

    def __str__(self):
        return f"{self.name} ({self.employee_id}) - {self.corporate.name}"

    @property
    def consultation_remaining(self):
        if self.plan and self.plan.consultation_limit > 0:
            return max(0, self.plan.consultation_limit - self.consultations_used)
        return None  # Unlimited

    @property
    def diagnostic_remaining(self):
        if self.plan and self.plan.diagnostic_limit > 0:
            return max(0, self.plan.diagnostic_limit - self.diagnostic_amount_used)
        return None  # Unlimited


class CorporateEmployeeDependant(BaseModel):
    """
    Dependants of corporate employees covered under plans.
    """
    employee = models.ForeignKey(
        CorporateEmployee,
        on_delete=models.CASCADE,
        related_name='dependants'
    )

    RELATION_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('parent_in_law', 'Parent-in-Law'),
    ]

    name = models.CharField(max_length=255)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)

    # Link to dependant in main system
    dependant = models.ForeignKey(
        'dependants.Dependant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'corporate_employee_dependants'

    def __str__(self):
        return f"{self.name} ({self.relation}) - {self.employee.name}"


class CorporateBookingApproval(BaseModel):
    """
    Approval workflow for corporate employee bookings.
    """
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='corporate_approvals'
    )
    employee = models.ForeignKey(
        CorporateEmployee,
        on_delete=models.CASCADE,
        related_name='booking_approvals'
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('auto_approved', 'Auto Approved'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corporate_approvals_given'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'corporate_booking_approvals'

    def __str__(self):
        return f"{self.case.case_id} - {self.status}"


class CorporateInvoice(BaseModel):
    """
    Invoices generated for corporate clients.
    """
    corporate = models.ForeignKey(Corporate, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()

    # Billing Period
    period_start = models.DateField()
    period_end = models.DateField()

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Files
    invoice_file = models.FileField(upload_to='corporate_invoices/', blank=True, null=True)

    # Notes
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'corporate_invoices'
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.corporate.name}"
