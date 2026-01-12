from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
import uuid
from django.conf import settings
from apps.location.models import State , City
from apps.dependants.models import Dependant
from apps.common.models import BaseModel
from apps.addresses.models import Address

User = settings.AUTH_USER_MODEL


# EYE TREATMENTS
class EyeTreatment(BaseModel):
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    detailed_description = models.TextField(blank=True)
    image = models.ImageField(upload_to="eye_treatments/", blank=True, null=True)

    def __str__(self):
        return self.name


# DENTAL TREATMENTS
class DentalTreatment(BaseModel):
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    detailed_description = models.TextField(blank=True)
    image = models.ImageField(upload_to="dental_treatments/", blank=True, null=True)

    def __str__(self):
        return self.name




# class EyeVendorAddress(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="eye_addresses")
#     address = models.TextField()
#     consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

#     def __str__(self):
#         return f"{self.vendor.name} - {self.address}"


# class DentalVendorAddress(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="dental_addresses")
#     address = models.TextField()
#     consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

#     def __str__(self):
#         return f"{self.vendor.name} - {self.address}"




# class EyeDentalVoucher(models.Model):

#     SERVICE_TYPE = [
#         ("eye", "Eye Care"),
#         ("dental", "Dental Care"),
#     ]

#     BOOKING_FOR = [
#         ("self", "Self"),
#         ("dependant", "Dependant"),
#     ]

    
#     request_id = models.CharField(max_length=20, unique=True, editable=False)

#     user = models.ForeignKey(User , on_delete=models.CASCADE)

#     booking_for = models.CharField(max_length=20, choices=BOOKING_FOR, default="self")
#     dependant_name = models.CharField(max_length=255, blank=True, null=True)
#     # dependant_relationship = models.CharField(max_length=255, blank=True, null=True)

#     service_type = models.CharField(max_length=20, choices=SERVICE_TYPE)

#     # Treatments
#     eye_treatment = models.ForeignKey(EyeTreatment, null=True, blank=True, on_delete=models.SET_NULL)
#     dental_treatment = models.ForeignKey(DentalTreatment, null=True, blank=True, on_delete=models.SET_NULL)

   

#     # User / dependant details
#     name = models.CharField(max_length=255)
#     contact_number = models.CharField(max_length=20)
#     email = models.EmailField()
#     state = models.CharField(max_length=255)
#     city = models.CharField(max_length=255)
#     address = models.TextField()

#     created_at = models.DateTimeField(auto_now_add=True)

    


# EYE TREATMENT BOOKING


# class EyeRequest(BaseModel):

#     SERVICE_TYPE_CHOICES = [
#     ("online", "Online / Video Consultation"),
#     ("in_clinic", "Visit the center in person"),
# ]

#     BOOKING_FOR = [
#         ("self", "Self"),
#         ("dependant", "Dependant"),
#     ]

#     request_id = models.CharField(max_length=20, unique=True, editable=False)

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="eye_vouchers"
#     )

#     booking_for = models.CharField(
#         max_length=20,
#         choices=BOOKING_FOR,
#         default="self"
#     )

#     service_type = models.CharField(
#         max_length=20,
#         choices=SERVICE_TYPE_CHOICES
#     )


#     dependant = models.ForeignKey(
#         Dependant,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     eye_treatment = models.ForeignKey(
#         EyeTreatment,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     name = models.CharField(max_length=255)
#     contact_number = models.CharField(max_length=20)
#     email = models.EmailField()

#     state = models.ForeignKey(
#         State,
#         on_delete=models.SET_NULL,
#         null=True
#     )

#     city = models.ForeignKey(
#         City,
#         on_delete=models.SET_NULL,
#         null=True
#     )

#     address = models.TextField()
    

#     def __str__(self):
#         return f"Eye Voucher - {self.request_id}"

# DENTAL TREATMENT BOOKING

# class DentalRequest(BaseModel):


#     SERVICE_TYPE_CHOICES = [
#     ("online", "Online / Video Consultation"),
#     ("in_clinic", "Visit the center in person"),
# ]

#     BOOKING_FOR = [
#         ("self", "Self"),
#         ("dependant", "Dependant"),
#     ]

#     request_id = models.CharField(max_length=20, unique=True, editable=False)

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="dental_vouchers"
#     )

#     booking_for = models.CharField(
#         max_length=20,
#         choices=BOOKING_FOR,
#         default="self"
#     )


#     service_type = models.CharField(
#         max_length=20,
#         choices=SERVICE_TYPE_CHOICES
#     )

#     dependant = models.ForeignKey(
#         Dependant,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     dental_treatment = models.ForeignKey(
#         DentalTreatment,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     name = models.CharField(max_length=255)
#     contact_number = models.CharField(max_length=20)
#     email = models.EmailField()

#     state = models.ForeignKey(
#         State,
#         on_delete=models.SET_NULL,
#         null=True
#     )

#     city = models.ForeignKey(
#         City,
#         on_delete=models.SET_NULL,
#         null=True
#     )

#     address = models.TextField()
    

#     def __str__(self):
#         return f"Dental Voucher - {self.request_id}"




class EyeDentalCareBooking(BaseModel):
     
    CARE_PROGRAM_TYPE = [
        ("eye", "Eye Care"),
        ("dental", "Dental Care"),
    ]

    BOOKING_TYPE_CHOICES = [
    ("treatment", "Treatment"),
    ("book_appointment", "Book Appointment"),

]
    
    SERVICE_TYPE_CHOICES = [
    ("online", "Online / Video Consultation"),
    ("in_clinic", "Visit the center in person"),
]

      
    FOR_WHOM_CHOICES = [
        ("self", "Self"),
        ("dependant", "Dependant"),
    ]

  


    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("callback_requested", "Callback Requested"),
    ]


    care_program_type = models.CharField(max_length=20, choices=CARE_PROGRAM_TYPE)

    booking_type = models.CharField(
    max_length=20,
    choices=BOOKING_TYPE_CHOICES,
)

    eye_treatment = models.ForeignKey(
        EyeTreatment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eye_care_bookings",
    )

    dental_treatment = models.ForeignKey(
        DentalTreatment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dental_care_bookings",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="eye_dental_care_bookings",
    )

    for_whom = models.CharField(
        max_length=20,
        choices=FOR_WHOM_CHOICES,
        default="self",
    )

    dependant = models.ForeignKey(
        Dependant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eye_dental_care_bookings",
    )

    name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()

    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eye_dental_care_bookings",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eye_dental_care_bookings",
    )
    address_text = models.TextField()

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eye_dental_care_bookings",
    )

    service_type = models.CharField(
        max_length=100,
        choices=SERVICE_TYPE_CHOICES,
    )

    requirements = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service_type} booking for {self.name} ({self.status})"
