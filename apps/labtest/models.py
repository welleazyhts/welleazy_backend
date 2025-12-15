from django.db import models
from apps.common.models import BaseModel
from apps.location.models import City
from apps.labfilter.models import VisitType
from django.conf import settings
User=settings.AUTH_USER_MODEL

class Test(BaseModel):
    user= models.ForeignKey(User, on_delete=models.CASCADE, related_name="lab_tests", null=True, blank=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(default=True)
    # status=models.CharField(max_length =50, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code or 'N/A'})"
    
    def __str__(self):
        return f"LabTest {self.code}"


# class DiagnosticCenter(BaseModel):
#     name = models.CharField(max_length=255)
#     code = models.CharField(max_length=100, blank=True, null=True)
#     address = models.TextField(blank=True, null=True)
#     area = models.CharField(max_length=255, blank=True, null=True)  
#     pincode = models.CharField(max_length=10, blank=True, null=True) 
#     contact_number = models.CharField(max_length=20, blank=True, null=True)
#     email = models.EmailField(blank=True, null=True)
#     active = models.BooleanField(default=True)
#     city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="diagnostic_centers")
#     tests = models.ManyToManyField(Test, related_name="diagnostic_centers")
#     visit_types = models.ManyToManyField(VisitType, related_name="diagnostic_centers", blank=True)


#     def __str__(self):
#         return f"{self.name} ({self.code or 'N/A'})"
