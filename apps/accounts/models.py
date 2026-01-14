from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import random
import hashlib
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        # Generate unique IDs
        user.member_id = self.generate_member_id()
        user.employee_id = self.generate_employee_id()
        user.save(using=self._db)

        # Create related profile only (no default addresses)
        UserProfile.objects.create(user=user)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

    def generate_member_id(self):
        while True:
            code = f"WZ_{random.randint(100000, 999999)}"
            if not User.objects.filter(member_id=code).exists():
                return code

    def generate_employee_id(self):
        while True:
            code = f"WEZ{random.randint(100000, 999999)}"
            if not User.objects.filter(employee_id=code).exists():
                return code

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15, unique=True)
    member_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["mobile_number"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        # Auto-generate member_id if missing
        if not self.member_id:
            while True:
                new_member_id = f"WZ_{random.randint(100000, 999999)}"
                if not User.objects.filter(member_id=new_member_id).exists():
                    self.member_id = new_member_id
                    break

        # Auto-generate employee_id if missing
        if not self.employee_id:
            while True:
                new_employee_id = f"WEZ{random.randint(100000, 999999)}"
                if not User.objects.filter(employee_id=new_employee_id).exists():
                    self.employee_id = new_employee_id
                    break

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class PasswordResetToken(models.Model):
    # Persistent token for password reset
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_token(cls, user):
        token = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(minutes=15)
        return cls.objects.create(user=user, token=token, expires_at=expires)

    def is_valid(self):
        return (not self.is_used) and timezone.now() < self.expires_at

    def mark_used(self):
        self.is_used = True
        self.save()

class UserOTP(models.Model):
    METHOD_CHOICES = (
        ('email', 'Email'),
        ('mobile', 'Mobile'),
    )

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="otps")
    identifier = models.CharField(max_length=100)  # email or mobile number
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    otp_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_otp(cls, user, method, identifier):
        otp_plain = str(random.randint(100000, 999999))
        otp_hash = hashlib.sha256(otp_plain.encode()).hexdigest()
        expires = timezone.now() + timedelta(minutes=10)
        cls.objects.create(user=user, method=method, identifier=identifier, otp_hash=otp_hash, expires_at=expires)
        return otp_plain  # return plain OTP to send

    def is_valid(self):
        return (not self.is_used) and timezone.now() < self.expires_at

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    personal_email = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    corporate_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
