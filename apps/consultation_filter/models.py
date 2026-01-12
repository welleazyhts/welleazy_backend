from django.db import models
from apps.common.models import BaseModel
# from django.contrib.auth.models import User
from django.conf import settings
from apps.location.models import City
from django.core.validators import RegexValidator


# Create your models here.


# DOCTOR SPECIALIZATIONS
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


# LANGUAGE SELECTION

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
        return f"{self.user.username} -> {self.language}"


    # PINCODES

class Pincode(BaseModel):
    code = models.CharField(max_length=6, unique=True, validators=[RegexValidator(r'^\d{6}$', 'Enter a valid 6-digit pincode')])
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="pincodes")
   


    class Meta:
        db_table="pincodes"

    def __str__(self):
        return f"{self.code} - {self.city.name}"
    
   



    # VENDOR LIST

class Vendor(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    available = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    external_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    specialization=models.ForeignKey(DoctorSpeciality , on_delete=models.CASCADE , null=True , blank=True)

    class Meta:
        db_table='vendors'

    def __str__(self):
        return self.name




