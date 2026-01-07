from django.db import models
from apps.common.models import BaseModel
from apps.labtest.models import Test
from django.conf import settings 
User= settings.AUTH_USER_MODEL


class HealthPackage(BaseModel):



    HEALTH_PACKAGE_TYPES = [
        ("annual_health_package", "Annual Health Packages"),
        ("special_package", "Special Packages"),
        ("regular_package", "Regular Packages"),
    ]
    user= models.ForeignKey(User, on_delete=models.CASCADE, related_name="health_packages", null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    validity_till = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0) 
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default="active")
    package_type = models.CharField(max_length=50, choices=HEALTH_PACKAGE_TYPES, default="regular_package")
    

    # Relationship with tests
    tests = models.ManyToManyField(Test, related_name='health_packages', blank=True)

    def __str__(self):
        return f"{self.name} ({self.code or 'N/A'})"
