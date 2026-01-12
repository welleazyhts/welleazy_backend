from django.db import models
from apps.common.models import BaseModel
from django.conf import settings
User=settings.AUTH_USER_MODEL

from apps.pharmacy.models import Medicine

# Create your models here.

class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pharmacy_cart")
    coupon = models.ForeignKey("Coupon", null=True, blank=True, on_delete=models.SET_NULL)
    
    DELIVERY_CHOICES= (
        ("home_delivery", "Home Delivery"),
        ("cod", "Cash on Delivery"),
       
    )
    delivery_mode=models.CharField(max_length=20, choices=DELIVERY_CHOICES, default="home_delivery")
    @property
    def total_mrp(self):
        return sum(item.medicine.mrp_price * item.quantity for item in self.items.all())

    @property
    def total_selling(self):
        return sum(item.medicine.selling_price * item.quantity for item in self.items.all())

    @property
    def discount_on_mrp(self):
        return self.total_mrp - self.total_selling

    @property
    def handling_fee(self):
        return 12

    @property
    def platform_fee(self):
        return 5   # or 0 -> if you want no platform fee

    @property
    def delivery_charge(self):
        return 79

    @property
    def coupon_discount(self):
        if self.coupon:
            return self.coupon.calculate_discount(self.total_selling)
        return 0

    @property
    def total_pay(self):
        return (
            self.total_selling
            + self.handling_fee
            + self.platform_fee
            + self.delivery_charge
            - self.coupon_discount
        )

    address=models.ForeignKey("addresses.Address", on_delete=models.SET_NULL, null=True, blank=True)

    prescription=models.ForeignKey("Prescription", on_delete=models.SET_NULL, null=True, blank=True)

class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "medicine")


class Coupon(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.IntegerField(default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_cart_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_discount(self, cart_total):
        if cart_total < self.min_cart_value:
            return 0

        if self.discount_percent > 0:
            return (cart_total * self.discount_percent) / 100

        return self.discount_amount

    def __str__(self):
        return self.code


class Prescription(BaseModel):
    PRESCREPTION_TYPES =(
        ("uploaded", "Uploaded Prescreption"),
        ("e_prescreption", "E-Prescreption" ),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prescriptions")
    file = models.FileField(upload_to="pharmacy/prescriptions/")
    notes = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=PRESCREPTION_TYPES, default="uploaded")

    # For E-Prescreption
    doctor_name = models.CharField(max_length=255, blank=True, null=True)
    diagnosis= models.CharField(max_length=255, blank=True, null=True)
    prescribed_date = models.DateField(blank=True, null=True)

   

    def __str__(self):
        return f"{self.user} - {self.type}"
