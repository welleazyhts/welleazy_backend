from django.db import models

# Create your models here.

from apps.consultation_filter.models import DoctorSpeciality,Language,Vendor
from apps.common.models import BaseModel
from apps.location.models import City 


from django.conf import settings
User=settings.AUTH_USER_MODEL
class DoctorPersonalDetails(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doctor_personal")
    city = models.ForeignKey(City , on_delete=models.CASCADE , blank=True)
    full_name = models.CharField(max_length=150)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female')])
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField()
    age=models.IntegerField()
    blood_group=models.CharField(max_length=5)
    address = models.TextField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to="doctor_profiles/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table="doctor_personal_details"

    def __str__(self):
        return self.full_name
    


class DoctorProfessionalDetails(BaseModel):

    doctor = models.OneToOneField(
        DoctorPersonalDetails,
        on_delete=models.CASCADE,
        related_name="professional"
    )

    # All ForeignKeys as required by you
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, related_name="doctors")
    specialization = models.ManyToManyField(DoctorSpeciality, blank=True, related_name="doctors")
    language = models.ManyToManyField(Language, blank=True, related_name="doctors")
    qualification=models.CharField(max_length=100,null=True , blank=True)

    experience_years = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    license_number = models.CharField(max_length=100, unique=True)
    clinic_address = models.TextField(null=True, blank=True)
    e_consultation = models.BooleanField(null=True, blank=True)
    in_clinic = models.BooleanField(null=True, blank=True)
    

    class Meta:
        db_table="doctor_professional_details"

    def __str__(self):
        return f"{self.doctor.full_name} - {self.specialization}"


# class DoctorPrescription(BaseModel):
#     appointment = models.OneToOneField(
#         Appointment,
#         on_delete=models.CASCADE,
#         related_name='doctor_prescription'
#     )
#     doctor = models.ForeignKey(
#         'doctor_details.DoctorProfessionalDetails',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     notes = models.TextField(null=True, blank=True)
#     prescription_file = models.FileField(
#         upload_to="doctor_prescriptions/",
#         null=True,
#         blank=True
#     )
    
#     def __str__(self):
#         return f"Prescription for Appointment #{self.appointment.id}"