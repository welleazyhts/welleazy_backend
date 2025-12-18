from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from django.utils import timezone
from datetime import timedelta
import random
import hashlib

User = settings.AUTH_USER_MODEL


class RelationshipType(BaseModel):
    # Stores relationship categories like Spouse, Child, etc.
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Relationship Type"
        verbose_name_plural = "Relationship Types"

    def __str__(self):
        return self.name


class DependantManager(models.Manager):
    def create_dependant(self, user, **extra_fields):
        dependant = self.model(user=user, **extra_fields)
        dependant.member_id = self.generate_member_id()
        dependant.save(using=self._db)
        return dependant

    def generate_member_id(self):
        while True:
            code = f"WZD{random.randint(100000, 999999)}"
            if not self.model.objects.filter(member_id=code).exists():
                return code



RELATIONSHIP_CHOICES = [
    ("Spouse", "Spouse"),
    ("Child", "Child"),
    
    ("Parent", "Parent"),
    ("Wife","Wife"),
    ("Other", "Other"),
]



class Dependant(BaseModel):
    #Dependant model linked to User and RelationshipType

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dependants")
    member_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    relationship = models.ForeignKey(RelationshipType, on_delete=models.SET_NULL, null=True, related_name="dependants")
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    objects = DependantManager()

    def save(self, *args, **kwargs):
        if not self.member_id:
            self.member_id = Dependant.objects.generate_member_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.relationship}) of {self.user.email}"


class DependantOTP(models.Model):
    #OTP model for dependant profile switch verification
    
    dependant = models.ForeignKey(Dependant, on_delete=models.CASCADE, related_name="otps")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dependant_otps")
    otp_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Dependant OTP"
        verbose_name_plural = "Dependant OTPs"
        ordering = ['-created_at']

    @classmethod
    def create_otp(cls, dependant, user):
        #Create OTP for dependant verification. Using static OTP '123456' for now.
        # TODO: Replace with dynamic OTP when Twilio is configured
        otp_plain = random.randint(100000, 999999)  # Static OTP for testing
        otp_hash = hashlib.sha256(str(otp_plain).encode()).hexdigest()
        expires = timezone.now() + timedelta(minutes=10)
        
        # Invalidate any previous unused OTPs for this dependant
        cls.objects.filter(
            dependant=dependant, 
            user=user, 
            is_used=False
        ).update(is_used=True)
        
        cls.objects.create(
            dependant=dependant, 
            user=user, 
            otp_hash=otp_hash, 
            expires_at=expires
        )
        return otp_plain

    def is_valid(self):
        #Check if OTP is still valid (not used and not expired)
        return (not self.is_used) and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.dependant.name} - {'Used' if self.is_used else 'Active'}"


class ProfileSwitch(models.Model):
    #Track active profile switches for users.
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile_switches")
    dependant = models.ForeignKey(Dependant, on_delete=models.CASCADE, related_name="profile_switches")
    switched_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Profile Switch"
        verbose_name_plural = "Profile Switches"
        ordering = ['-switched_at']
        # Ensure only one active switch per user
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True),
                name='unique_active_switch_per_user'
            )
        ]

    def activate(self):
        #Activate this switch and deactivate all others for the same user.
        ProfileSwitch.objects.filter(user=self.user, is_active=True).exclude(id=self.id).update(is_active=False)
        self.is_active = True
        self.save()

    def deactivate(self):
        #Deactivate this profile switch.
        self.is_active = False
        self.save()

    @classmethod
    def get_active_switch(cls, user):
        #Get the active profile switch for a user, if any.
        try:
            return cls.objects.get(user=user, is_active=True)
        except cls.DoesNotExist:
            return None

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.user.email} -> {self.dependant.name} ({status})"
    