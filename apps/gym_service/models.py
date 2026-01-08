from django.db import models

# Create your models here.



from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from apps.dependants.models import Dependant
from apps.location.models import City, State 

User = settings.AUTH_USER_MODEL

class GymCenter(models.Model):
    
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=64, blank=True, null=True)  # e.g. GX
    business_line = models.CharField(max_length=128, blank=True, null=True)  # e.g. ELITE
    address = models.TextField(blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    # logo or center image
    logo = models.ImageField(upload_to='gym_service/logos/', blank=True, null=True)  # store URL/path (or use ImageField with media)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GymPackage(models.Model):
    
    title = models.CharField(max_length=255)          # e.g. "3 MONTHS"
    duration_months = models.PositiveSmallIntegerField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    features = models.CharField(max_length=500 , default=list)         # list of features/strings
    created_at = models.DateTimeField(auto_now_add=True)
    vendor_logo = models.ImageField(upload_to='gym_service/packages/vendor_logo', blank=True, null=True)  # example: store URL/path

    def __str__(self):
        return f"{self.title} ({self.duration_months} months)"



class Voucher(models.Model):
    
    VOUCHER_STATUS = [
        ('pending', 'Pending'),     # waiting for activation/activation code
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    voucher_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gym_vouchers")
    package = models.ForeignKey(GymPackage, on_delete=models.PROTECT)
    gym_center = models.ForeignKey(GymCenter, on_delete=models.PROTECT)
    # type: self or dependant
    booking_for = models.CharField(max_length=16, choices=[('self','Self'), ('dependant','Dependant')], default='self')
    dependant = models.ForeignKey(Dependant, on_delete=models.SET_NULL, blank=True, null=True)
    contact_number = models.CharField(max_length=32, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=1024, blank=True, null=True)

    # business fields
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default='INR')
    status = models.CharField(max_length=16, choices=VOUCHER_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(blank=True, null=True)

    def voucher_id_display(self):
        # human-friendly short id (e.g. #42) - or use pk
        return f"#{self.pk}"

    def __str__(self):
        return f"Voucher {self.voucher_uuid} for {self.user}"
