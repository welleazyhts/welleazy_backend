from django.db import models
from apps.common.models import BaseModel
from django.conf import settings
from apps.labtest.models import Test
from apps.diagnostic_center.models import DiagnosticCenter
from apps.labfilter.models import VisitType
from apps.addresses.models import Address
from apps.dependants.models import Dependant
from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage
from datetime import time
from apps.doctor_details.models import DoctorProfessionalDetails
from apps.consultation_filter.models import DoctorSpeciality , Vendor

import random

import uuid

User = settings.AUTH_USER_MODEL


class ReportDocument(models.Model):
    
    file = models.FileField(upload_to="appointment_reports/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.id}"


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts", null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_item(self, **kwargs):
        return CartItem.objects.create(cart=self, **kwargs)

class CartItem(BaseModel):
    ITEM_TYPE_CHOICES = (
        ("test", "Test"),
        ("health_package", "Health Package"),
        ("sponsored_package", "Sponsored Package"),
        ("appointment", "Lab Appointment"),
        ("doctor_appointment","Doctor Appointment"),
        ("dental_appointment" , "Dental Appointment"),
        ("eye_appointment" , "Eye Appointment"),
    )

    MODE_CHOICES = [
        ('video', 'Video Consultation'),
        ('tele', 'Telephonic Consultation'),
        ('in-person' , 'In-Person Consultation'),
    ]

    # SERVICE_TYPES = [
    #     ("eye" , "Eye"),
    #     ("dental","Dental"),
    # ]

    user=models.ForeignKey(User , on_delete=models.CASCADE , null=True , blank=True)
    FOR_WHOM_CHOICES = (
        ("self", "Self"),
        ("dependant", "Dependant"),
    )

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", null=True)
    item_type = models.CharField(max_length=30, choices=ITEM_TYPE_CHOICES, default="test")
    

    # common fields
    diagnostic_center = models.ForeignKey(DiagnosticCenter, on_delete=models.CASCADE,null=True)
    for_whom = models.CharField(
        max_length=20,
        choices=FOR_WHOM_CHOICES,
        default="self",
    )
    dependant = models.ForeignKey(Dependant, on_delete=models.SET_NULL, null=True, blank=True)

    # for tests
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, null=True, blank=True)
    tests = models.ManyToManyField(Test, blank=True)
    address = models.ForeignKey("addresses.Address", on_delete=models.SET_NULL, null=True, blank=True)

    # for packages
    health_package = models.ForeignKey(HealthPackage, on_delete=models.CASCADE, null=True, blank=True)
    sponsored_package = models.ForeignKey(SponsoredPackage, on_delete=models.CASCADE, null=True, blank=True)

    note = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    # for doctor-appointment

    doctor=models.ForeignKey(DoctorProfessionalDetails , null=True , blank=True , on_delete=models.CASCADE)
    def generate_appointment_code():
        return random.randint(10000, 999999)  # 5–6 digit random number
    appointment_id = models.CharField(  unique=True , default=generate_appointment_code, editable=False , null=True , blank=True)
    specialization = models.ForeignKey(DoctorSpeciality, on_delete=models.CASCADE, related_name="eyedentalcare_specialization", blank=True , null=True)
    patient_name = models.CharField(max_length=150 , blank=True)
    symptoms = models.TextField(max_length=1000, blank=True )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES , null=True , blank=True)
    for_whom = models.CharField(max_length=20, choices=FOR_WHOM_CHOICES , default="self" )
    appointment_date = models.DateField(null=True)
    appointment_time = models.TimeField(null=True)
    booked_on = models.DateTimeField(auto_now_add=True, null=True)
    documents=models.ManyToManyField(ReportDocument, blank=True, related_name="appointments")
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)


    #EYE DENTAL CARE APPOINTMENTS----
  
    # Service_type=models.CharField(max_length=20 , choices=SERVICE_TYPES , null=True , blank=True)
    # vendor = models.ForeignKey(Vendor , on_delete=models.CASCADE , null=True , blank=True)
    # eye_vendor_centers= models.ForeignKey(EyeVendorAddress , on_delete= models.CASCADE , null=True , blank=True)
    # dental_vendor_centers = models.ForeignKey(DentalVendorAddress , on_delete=models.CASCADE , null=True , blank=True)
   

    # USED ONLY FOR LABTEST
    selected_date=models.DateField(null=True , blank=True) 
    selected_time=models.TimeField(null=True , blank=True) 
    slot_confirmed=models.BooleanField(default=False) 
    
    def apply_discount(self):
        base_price = self.price or 0
        discount = 0

        # Health Package discount
        if self.item_type == "health_package" and self.health_package:
            discount = self.health_package.discount_amount or 0

        # Sponsored Package discount
        if self.item_type == "sponsored_package" and self.sponsored_package:
            discount = self.sponsored_package.discount_amount or 0

        # Diagnostic Center Percentage Discount
        if self.diagnostic_center and getattr(self.diagnostic_center, "discount_percent", 0):
            discount += base_price * (self.diagnostic_center.discount_percent / 100)

        # Final store
        self.discount_amount = discount
        self.final_price = max(base_price - discount, 0)
        self.save()

        return self

    def __str__(self):
        return f"CartItem({self.id}, {self.item_type})"
    
    def __str__(self):
        return f"{self.item_type} item - {self.appointment or self.doctor}"


    def __str__(self):
        return f"{self.item_type} item - {self.diagnostic_center.name}"
    
class Appointment(BaseModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )
   


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_main" , null=True)
    diagnostic_center = models.ForeignKey(DiagnosticCenter, on_delete=models.CASCADE , null=True)
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE , null=True)
    for_whom = models.CharField(
        max_length=20,
        choices=CartItem.FOR_WHOM_CHOICES,
        default="self",
    )
    item_type= models.CharField(max_length=30, choices=CartItem.ITEM_TYPE_CHOICES, default="test")
    dependant = models.ForeignKey(Dependant, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointment_created_main")
    address = models.ForeignKey("addresses.Address", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    scheduled_at = models.DateTimeField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    note = models.TextField(blank=True, null=True)

    # DOCTOR APPOINTMENT----

    doctor=models.ForeignKey(DoctorProfessionalDetails , null=True , blank=True , on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=150 , blank=True , null=True)
    mode=models.CharField(max_length=10, choices=CartItem.MODE_CHOICES , null=True , blank=True)

    # EYE & DENTAL APPOINTMENT----

    # vendor = models.ForeignKey(Vendor , on_delete=models.CASCADE , null=True , blank=True)
    # eye_vendor_centers= models.ForeignKey(EyeVendorAddress , on_delete= models.CASCADE , null=True , blank=True)
    # dental_vendor_centers = models.ForeignKey(DentalVendorAddress , on_delete=models.CASCADE , null=True , blank=True)


    # PAYMENT RELATED----

    payment_mode = models.CharField(max_length=50, null=True, blank=True)  
    payment_bank = models.CharField(max_length=100, null=True, blank=True)
    payment_reference = models.CharField(max_length=200, null=True, blank=True)
    payment_transaction_id = models.CharField(max_length=200, null=True, blank=True)
    payment_last4 = models.CharField(max_length=10, null=True, blank=True)  # Card/UPI last digits


    prescription= models.FileField(upload_to="prescriptions/" , null=True , blank=True)
   

    

    @property
    def confirmed(self):
        return self.status.lower() == 'confirmed'

class AppointmentItem(BaseModel):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="items", null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True)
    doctor=models.ForeignKey(DoctorProfessionalDetails , on_delete=models.CASCADE , null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)


# DOCTOR RELATED-----

class DoctorAvailability(models.Model):

    MODE_CHOICES = [
        ("tele", "Tele Consultation"),
        ("video", "Video Consultation"),
    ]
    
    doctor = models.ForeignKey(DoctorProfessionalDetails, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])

    mode=models.CharField(max_length=10 , choices=MODE_CHOICES)

    date=models.DateField()
    start_time = models.TimeField(default=time(9, 0))
    end_time = models.TimeField(default=time(17, 0))
    break_start = models.TimeField(default=time(13, 0))
    break_end = models.TimeField(default=time(14, 0))
    slot_duration = models.IntegerField(default=30)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "mode", "date","start_time", "end_time"],
                name="unique_doctor_mode_date_time",
                  
            ),
            
        ]
    def save(self, *args, **kwargs):
       
        if self.date:
            self.day_of_week = self.date.strftime("%A")  # Converts -> Monday / Tuesday
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doctor.doctor.full_name} - {self.mode} - {self.date} ({self.day_of_week})"
    




class AppointmentVoucher(BaseModel):
    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE, related_name='voucher')
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voucher for {self.appointment.patient_name}"
    

class MedicalReports(BaseModel):
    appointment= models.ForeignKey(Appointment , on_delete=models.CASCADE, related_name="medical_reports")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to="medical_reports/")
    uploaded_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Appointment {self.appointment.id}"


