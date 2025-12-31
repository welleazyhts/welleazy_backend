from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.appointments.models import Appointment
from apps.consultation_filter.models import Vendor
from apps.diagnostic_center.models import DiagnosticCenter
import uuid

User = settings.AUTH_USER_MODEL


def generate_case_id():
    """Generate unique case ID like WX12345"""
    import random
    return f"WX{random.randint(10000, 99999)}"


class Case(BaseModel):
    """
    Central case management model for tracking all service requests.
    Links appointments, vendors, and operations workflow.
    """
    SERVICE_TYPE_CHOICES = [
        ('diagnostic', 'Diagnostic Test'),
        ('consultation', 'Doctor Consultation'),
        ('pharmacy', 'Pharmacy Order'),
        ('health_package', 'Health Package'),
        ('sponsored_package', 'Sponsored Package'),
        ('eye_care', 'Eye Care'),
        ('dental_care', 'Dental Care'),
        ('gym', 'Gym/Fitness'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('pending_vendor', 'Pending Vendor Response'),
        ('scheduled', 'Scheduled'),
        ('sample_collected', 'Sample Collected'),
        ('report_pending', 'Report Pending'),
        ('report_uploaded', 'Report Uploaded'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    SOURCE_CHOICES = [
        ('app', 'Mobile App'),
        ('web', 'Website'),
        ('crm', 'CRM Manual Entry'),
        ('api', 'External API'),
        ('call', 'Call Center'),
        ('email', 'Email'),
        ('walkin', 'Walk-in'),
        ('hr_portal', 'HR Portal'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
        ('corporate', 'Corporate Billing'),
        ('insurance', 'Insurance'),
        ('cod', 'Cash on Delivery'),
    ]

    VISIT_TYPE_CHOICES = [
        ('home', 'Home Visit'),
        ('center', 'At Center'),
        ('video', 'Video Consultation'),
        ('hybrid', 'Hybrid'),
    ]

    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('corporate_employee', 'Corporate Employee'),
        ('dependant', 'Dependant'),
        ('hni', 'HNI/VIP'),
    ]

    # Unique Case Identifier
    case_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_case_id,
        editable=False,
        db_index=True
    )

    # Patient Information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cases',
        help_text="Customer/Patient who created this case"
    )
    patient_name = models.CharField(max_length=255)
    patient_phone = models.CharField(max_length=20, blank=True, null=True)
    patient_email = models.EmailField(blank=True, null=True)
    is_dependant = models.BooleanField(default=False)
    dependant = models.ForeignKey(
        'dependants.Dependant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases'
    )

    # Service Details
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases'
    )

    # Vendor Information
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases',
        help_text="Vendor handling this case"
    )
    vendor_booking_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Booking ID in vendor's system"
    )
    diagnostic_center = models.ForeignKey(
        DiagnosticCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases'
    )

    # Corporate/Employer (if applicable)
    corporate = models.ForeignKey(
        'corporates.Corporate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases',
        help_text="Corporate client if this is an employee booking"
    )
    employee_id = models.CharField(max_length=50, blank=True, null=True)

    # Status & Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    customer_type = models.CharField(max_length=30, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES, default='center')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='prepaid')

    # Case Entry Details (from .NET app)
    received_by_name = models.CharField(max_length=255, blank=True, null=True)
    received_by_phone = models.CharField(max_length=20, blank=True, null=True)
    received_by_email = models.EmailField(blank=True, null=True)
    received_by_department = models.CharField(max_length=100, blank=True, null=True)
    case_received_datetime = models.DateTimeField(null=True, blank=True)

    # For call center cases
    agent_name = models.CharField(max_length=255, blank=True, null=True)
    agent_employee_id = models.CharField(max_length=50, blank=True, null=True)
    agent_phone = models.CharField(max_length=20, blank=True, null=True)

    # Medical Details
    medical_tests = models.TextField(blank=True, null=True, help_text="Comma-separated test names")
    generic_tests = models.TextField(blank=True, null=True)
    application_number = models.CharField(max_length=100, blank=True, null=True)

    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Address (for home visits)
    address = models.ForeignKey(
        'addresses.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases'
    )
    address_text = models.TextField(blank=True, null=True)

    # Financial
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    home_visit_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employee_to_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount employee pays (rest covered by corporate)")
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
            ('refunded', 'Refunded'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    # Bank details for payments
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_branch = models.CharField(max_length=255, blank=True, null=True)
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    utr_number = models.CharField(max_length=100, blank=True, null=True)

    # Follow-up Scheduling
    followup_date = models.DateField(null=True, blank=True)
    followup_remark = models.TextField(blank=True, null=True)

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases',
        help_text="Operations executive assigned to this case"
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Additional Info
    notes = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes visible only to CRM users"
    )
    tags = models.JSONField(default=list, blank=True)

    # SLA Tracking
    sla_due_at = models.DateTimeField(null=True, blank=True)
    is_sla_breached = models.BooleanField(default=False)

    class Meta:
        db_table = 'cases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['status']),
            models.Index(fields=['service_type']),
            models.Index(fields=['vendor']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        return f"{self.case_id} - {self.patient_name} ({self.get_service_type_display()})"

    def save(self, *args, **kwargs):
        # Calculate final amount
        self.final_amount = self.total_amount - self.discount_amount
        super().save(*args, **kwargs)


class CaseItem(BaseModel):
    """
    Individual items within a case (tests, packages, services).
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='items')

    ITEM_TYPE_CHOICES = [
        ('test', 'Lab Test'),
        ('package', 'Health Package'),
        ('consultation', 'Consultation'),
        ('medicine', 'Medicine'),
        ('service', 'Service'),
    ]

    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.PositiveIntegerField(help_text="ID of the test/package/service")
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Vendor mapping
    vendor_item_id = models.CharField(max_length=100, blank=True, null=True)
    vendor_item_name = models.CharField(max_length=255, blank=True, null=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    class Meta:
        db_table = 'case_items'

    def __str__(self):
        return f"{self.case.case_id} - {self.item_name}"

    def save(self, *args, **kwargs):
        self.final_price = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)


class CaseRemark(BaseModel):
    """
    Audit trail for case updates and communications.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='remarks')

    REMARK_TYPE_CHOICES = [
        ('status_change', 'Status Change'),
        ('assignment', 'Assignment Change'),
        ('note', 'Note Added'),
        ('vendor_update', 'Vendor Update'),
        ('customer_contact', 'Customer Contact'),
        ('escalation', 'Escalation'),
        ('system', 'System Generated'),
    ]

    remark_type = models.CharField(max_length=20, choices=REMARK_TYPE_CHOICES, default='note')
    remark = models.TextField()

    # For status changes
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)

    # Visibility
    is_internal = models.BooleanField(default=True, help_text="Internal remarks not shown to customer")
    is_visible_to_vendor = models.BooleanField(default=False)

    class Meta:
        db_table = 'case_remarks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case.case_id} - {self.remark_type} by {self.created_by}"


class CaseAssignment(BaseModel):
    """
    Track assignment history for cases.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='assignment_history')
    assigned_from = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases_assigned_from'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cases_assigned_to'
    )
    reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'case_assignments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case.case_id} assigned to {self.assigned_to}"


class CaseDocument(BaseModel):
    """
    Documents attached to cases (reports, prescriptions, etc.).
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')

    DOCUMENT_TYPE_CHOICES = [
        ('prescription', 'Prescription'),
        ('lab_report', 'Lab Report'),
        ('invoice', 'Invoice'),
        ('id_proof', 'ID Proof'),
        ('insurance', 'Insurance Document'),
        ('other', 'Other'),
    ]

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='case_documents/')
    file_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Source
    uploaded_by_vendor = models.BooleanField(default=False)
    vendor_document_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'case_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case.case_id} - {self.document_type}"


class CaseStatusLog(BaseModel):
    """
    Complete status change history for compliance and tracking.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='case_status_changes'
    )
    reason = models.TextField(blank=True, null=True)
    is_system_change = models.BooleanField(default=False)

    class Meta:
        db_table = 'case_status_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case.case_id}: {self.from_status} -> {self.to_status}"


class ConsultationCase(BaseModel):
    """
    Extended model for consultation-specific cases (E-Consultation, Specialist, Face-to-Face).
    Links to the main Case model with additional consultation fields.
    """
    CONSULTATION_TYPE_CHOICES = [
        ('e_consultation', 'E-Consultation'),
        ('specialist', 'Specialist Consultation'),
        ('face_to_face', 'Face to Face'),
        ('video', 'Video Consultation'),
        ('chat', 'Chat Consultation'),
    ]

    CONSULTATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('doctor_assigned', 'Doctor Assigned'),
        ('scheduled', 'Scheduled'),
        ('waiting', 'Waiting for Patient'),
        ('in_progress', 'In Progress'),
        ('prescription_pending', 'Prescription Pending'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='consultation_details'
    )
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES)
    consultation_status = models.CharField(
        max_length=20,
        choices=CONSULTATION_STATUS_CHOICES,
        default='pending'
    )

    # Doctor Information
    doctor = models.ForeignKey(
        'doctor_details.DoctorProfessionalDetails',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultation_cases'
    )
    doctor_name = models.CharField(max_length=255, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)

    # Appointment Details
    appointment_datetime = models.DateTimeField(null=True, blank=True)
    consultation_duration = models.PositiveIntegerField(
        default=15,
        help_text="Duration in minutes"
    )
    meeting_link = models.URLField(blank=True, null=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    meeting_password = models.CharField(max_length=50, blank=True, null=True)

    # Patient Symptoms
    chief_complaint = models.TextField(blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    symptom_duration = models.CharField(max_length=100, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)

    # Consultation Notes (filled by doctor)
    diagnosis = models.TextField(blank=True, null=True)
    treatment_plan = models.TextField(blank=True, null=True)
    doctor_notes = models.TextField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True, null=True)

    # Consultation completed
    consultation_started_at = models.DateTimeField(null=True, blank=True)
    consultation_ended_at = models.DateTimeField(null=True, blank=True)
    actual_duration = models.PositiveIntegerField(null=True, blank=True)

    # Recording (for video consultations)
    recording_url = models.URLField(blank=True, null=True)
    recording_available = models.BooleanField(default=False)

    class Meta:
        db_table = 'consultation_cases'
        ordering = ['-appointment_datetime']

    def __str__(self):
        return f"{self.case.case_id} - {self.get_consultation_type_display()}"


class CasePrescription(BaseModel):
    """
    Prescriptions generated during consultations.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='prescriptions')
    consultation = models.ForeignKey(
        ConsultationCase,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prescriptions'
    )

    prescription_number = models.CharField(max_length=50, unique=True)
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions_given'
    )
    prescribed_by_name = models.CharField(max_length=255)
    prescribed_at = models.DateTimeField(auto_now_add=True)

    # Prescription Details
    diagnosis = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    advice = models.TextField(blank=True, null=True)

    # PDF/File
    prescription_file = models.FileField(
        upload_to='prescriptions/',
        null=True,
        blank=True
    )

    # Validity
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'case_prescriptions'
        ordering = ['-prescribed_at']

    def __str__(self):
        return f"{self.prescription_number} - {self.case.case_id}"

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            import random
            self.prescription_number = f"RX{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)


class PrescriptionMedicine(BaseModel):
    """
    Individual medicines in a prescription.
    """
    prescription = models.ForeignKey(
        CasePrescription,
        on_delete=models.CASCADE,
        related_name='medicines'
    )

    medicine_name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True, null=True)
    dosage = models.CharField(max_length=100)  # e.g., "500mg"
    frequency = models.CharField(max_length=100)  # e.g., "1-0-1" or "Twice daily"
    duration = models.CharField(max_length=100)  # e.g., "7 days"
    quantity = models.PositiveIntegerField(default=1)
    timing = models.CharField(max_length=100, blank=True, null=True)  # Before/After meals
    instructions = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'prescription_medicines'

    def __str__(self):
        return f"{self.medicine_name} - {self.dosage}"


class CaseEscalation(BaseModel):
    """
    Track case escalations for management review.
    """
    ESCALATION_LEVEL_CHOICES = [
        ('level_1', 'Level 1 - Team Lead'),
        ('level_2', 'Level 2 - Manager'),
        ('level_3', 'Level 3 - Senior Manager'),
        ('level_4', 'Level 4 - Director'),
    ]

    ESCALATION_REASON_CHOICES = [
        ('sla_breach', 'SLA Breach'),
        ('customer_complaint', 'Customer Complaint'),
        ('vendor_issue', 'Vendor Issue'),
        ('quality_issue', 'Quality Issue'),
        ('payment_issue', 'Payment Issue'),
        ('technical_issue', 'Technical Issue'),
        ('urgent_request', 'Urgent Request'),
        ('vip_customer', 'VIP Customer'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='escalations')
    escalation_number = models.CharField(max_length=50, unique=True)

    level = models.CharField(max_length=20, choices=ESCALATION_LEVEL_CHOICES)
    reason = models.CharField(max_length=30, choices=ESCALATION_REASON_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    description = models.TextField()
    escalated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='escalations_raised'
    )
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='escalations_received'
    )
    escalated_at = models.DateTimeField(auto_now_add=True)

    # Resolution
    resolution = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalations_resolved'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    # SLA for escalation
    target_resolution_time = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)

    class Meta:
        db_table = 'case_escalations'
        ordering = ['-escalated_at']

    def __str__(self):
        return f"{self.escalation_number} - {self.case.case_id}"

    def save(self, *args, **kwargs):
        if not self.escalation_number:
            import random
            self.escalation_number = f"ESC{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)


class QCReview(BaseModel):
    """
    Quality Check reviews for cases.
    """
    QC_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('rework', 'Sent for Rework'),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='qc_reviews')
    qc_number = models.CharField(max_length=50, unique=True)

    status = models.CharField(max_length=20, choices=QC_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qc_reviews_done'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Scores
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    documentation_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    process_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    communication_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Feedback
    observations = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    critical_issues = models.TextField(blank=True, null=True)

    # Rework
    rework_required = models.BooleanField(default=False)
    rework_reason = models.TextField(blank=True, null=True)
    rework_deadline = models.DateTimeField(null=True, blank=True)
    rework_completed = models.BooleanField(default=False)
    rework_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'case_qc_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.qc_number} - {self.case.case_id}"

    def save(self, *args, **kwargs):
        if not self.qc_number:
            import random
            self.qc_number = f"QC{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)


class QCChecklist(BaseModel):
    """
    QC Checklist items for standardized review.
    """
    CATEGORY_CHOICES = [
        ('documentation', 'Documentation'),
        ('process', 'Process Compliance'),
        ('communication', 'Communication'),
        ('technical', 'Technical'),
        ('customer_service', 'Customer Service'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    is_critical = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    # Applicable service types
    applicable_service_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of service types this checklist applies to"
    )

    class Meta:
        db_table = 'qc_checklists'
        ordering = ['category', 'order', 'name']

    def __str__(self):
        return f"{self.category} - {self.name}"


class QCChecklistResponse(BaseModel):
    """
    Individual responses to QC checklist items.
    """
    RESPONSE_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('na', 'Not Applicable'),
        ('partial', 'Partial'),
    ]

    qc_review = models.ForeignKey(
        QCReview,
        on_delete=models.CASCADE,
        related_name='checklist_responses'
    )
    checklist_item = models.ForeignKey(
        QCChecklist,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'qc_checklist_responses'
        unique_together = ['qc_review', 'checklist_item']

    def __str__(self):
        return f"{self.qc_review.qc_number} - {self.checklist_item.name}"


class TeleMERQuestionnaire(BaseModel):
    """
    Tele Medical Examination Report questionnaire for insurance/medical cases.
    """
    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='tele_mer'
    )
    consultation = models.ForeignKey(
        ConsultationCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tele_mer'
    )

    # Patient Vitals
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    pulse_rate = models.PositiveIntegerField(null=True, blank=True)

    # Medical History Questions (JSON for flexibility)
    medical_history_responses = models.JSONField(default=dict, blank=True)

    # Lifestyle Questions
    is_smoker = models.BooleanField(null=True, blank=True)
    smoking_frequency = models.CharField(max_length=100, blank=True, null=True)
    is_alcohol_consumer = models.BooleanField(null=True, blank=True)
    alcohol_frequency = models.CharField(max_length=100, blank=True, null=True)
    exercise_frequency = models.CharField(max_length=100, blank=True, null=True)

    # Family History
    family_history = models.JSONField(default=dict, blank=True)

    # Current Conditions
    current_medications = models.TextField(blank=True, null=True)
    known_allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)

    # Examination Notes
    general_appearance = models.TextField(blank=True, null=True)
    examination_findings = models.TextField(blank=True, null=True)
    doctor_remarks = models.TextField(blank=True, null=True)

    # Verification
    verified_by_doctor = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verifying_doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_tele_mers'
    )

    # Recording
    audio_recording = models.FileField(upload_to='tele_mer_recordings/', null=True, blank=True)
    video_recording = models.FileField(upload_to='tele_mer_recordings/', null=True, blank=True)

    class Meta:
        db_table = 'tele_mer_questionnaires'

    def __str__(self):
        return f"TeleMER - {self.case.case_id}"

    def save(self, *args, **kwargs):
        # Calculate BMI if height and weight are provided
        if self.height_cm and self.weight_kg:
            height_m = float(self.height_cm) / 100
            self.bmi = round(float(self.weight_kg) / (height_m * height_m), 2)
        super().save(*args, **kwargs)


class HealthCheckupRequest(BaseModel):
    """
    Health check-up requests (Annual Health Checkup, Corporate checkups, etc.)
    """
    REQUEST_TYPE_CHOICES = [
        ('annual', 'Annual Health Checkup'),
        ('pre_employment', 'Pre-Employment'),
        ('periodic', 'Periodic Checkup'),
        ('special', 'Special Checkup'),
        ('executive', 'Executive Health Checkup'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('report_pending', 'Report Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='health_checkup'
    )
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Package Details
    package_name = models.CharField(max_length=255)
    package_id = models.PositiveIntegerField(null=True, blank=True)
    tests_included = models.JSONField(default=list, blank=True)

    # Scheduling
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    actual_date = models.DateField(null=True, blank=True)
    actual_time = models.TimeField(null=True, blank=True)

    # Location
    center_name = models.CharField(max_length=255, blank=True, null=True)
    center_address = models.TextField(blank=True, null=True)
    is_home_collection = models.BooleanField(default=False)

    # For corporate
    hr_approval_required = models.BooleanField(default=False)
    hr_approved = models.BooleanField(default=False)
    hr_approved_by = models.CharField(max_length=255, blank=True, null=True)
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    # Reports
    report_generated = models.BooleanField(default=False)
    report_generated_at = models.DateTimeField(null=True, blank=True)
    report_shared_with_employee = models.BooleanField(default=False)
    report_shared_with_hr = models.BooleanField(default=False)

    # Summary
    overall_health_status = models.CharField(max_length=50, blank=True, null=True)
    critical_findings = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'health_checkup_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"AHC - {self.case.case_id}"


class CaseQueue(BaseModel):
    """
    Define different queues for case workflow management.
    """
    QUEUE_TYPE_CHOICES = [
        ('open', 'Open Cases'),
        ('assigned', 'Assigned Cases'),
        ('pending_vendor', 'Pending Vendor'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('escalated', 'Escalated'),
        ('qc_pending', 'QC Pending'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=100)
    queue_type = models.CharField(max_length=20, choices=QUEUE_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)

    # Filter criteria (stored as JSON)
    filter_criteria = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON filter criteria for this queue"
    )

    # Assignment
    assigned_team = models.CharField(max_length=100, blank=True, null=True)
    default_assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_queues'
    )

    # SLA
    sla_hours = models.PositiveIntegerField(default=24)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'case_queues'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
