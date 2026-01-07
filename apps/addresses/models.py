from django.db import models
from apps.common.models import BaseModel
from apps.accounts.models import User
from apps.dependants.models import Dependant, RelationshipType
from apps.location.models import State, City


class AddressType(BaseModel):
    #Stores address categories like Home, Office, etc.
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Address Type"
        verbose_name_plural = "Address Types"

    def __str__(self):
        return self.name


class Address(BaseModel):
    #Stores address for user or dependant
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses", null=True, blank=True)
    dependant = models.ForeignKey(Dependant, on_delete=models.CASCADE, related_name="addresses", null=True, blank=True)
    address_type = models.ForeignKey(AddressType, on_delete=models.SET_NULL, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="addresses")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="addresses")
    pincode = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    @property
    def full_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.landmark,
            f"{self.city.name if self.city else ''}, {self.state.name if self.state else ''} - {self.pincode}"
        ]
        return ", ".join([p for p in parts if p])

    # class Meta:
    #     unique_together = ("user", "dependant", "address_type")

    def __str__(self):
        target = self.user.name if self.user else self.dependant.name
        return f"{self.address_type} address of {target}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
