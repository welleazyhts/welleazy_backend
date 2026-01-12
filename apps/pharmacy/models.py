from django.db import models

# Create your models here.


from django.db import models
from apps.common.models import BaseModel
from django.conf import settings
User=settings.AUTH_USER_MODEL

class PharmacyVendor(BaseModel):
    VENDOR_TYPES = (
        ("online", "Online"),
        ("offline", "Offline"),
    )

    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="pharmacy/vendors/", blank=True, null=True)
    vendor_type = models.CharField(max_length=10, choices=VENDOR_TYPES)
    city=models.CharField(max_length=150, null=True , blank=True)
    phone=models.CharField(max_length=15, null=True, blank=True)
    email=models.EmailField(null=True, blank=True)

    def __str__(self):
        return self.name


class PharmacyCategory(BaseModel):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to="pharmacy/categories/", blank=True, null=True)

    def __str__(self):
        return self.name


class PharmacyBanner(BaseModel):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="pharmacy/banners/")
    discount_text = models.CharField(max_length=50, blank=True)
    button_text = models.CharField(max_length=50, default="Buy Now")

    def __str__(self):
        return self.title


class Medicine(BaseModel):
    name = models.CharField(max_length=255 , unique=True)
    description = models.TextField(blank=True)
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.IntegerField(default=0)

    category = models.ForeignKey(
        PharmacyCategory, on_delete=models.SET_NULL, null=True, related_name="medicines"
    )
    vendor = models.ForeignKey(
        PharmacyVendor, on_delete=models.SET_NULL, null=True, related_name="medicines"
    )

    stock_count = models.IntegerField(default=0)
    image = models.ImageField(upload_to="pharmacy/medicines/", blank=True, null=True)

    def __str__(self):
        return self.name
    


class MedicineDetails(BaseModel):
    medicine = models.OneToOneField(
        Medicine, on_delete=models.CASCADE, related_name="details"
    )

    # Detailed fields
    introduction = models.TextField(null=True, blank=True)
    uses = models.TextField(null=True, blank=True)
    benefits = models.TextField(null=True, blank=True)
    side_effects = models.TextField(null=True, blank=True)
    safety_advice = models.TextField(null=True, blank=True)
    quick_tips = models.TextField(null=True, blank=True)
    faqs = models.TextField(null=True, blank=True)
    related_lab_tests = models.TextField(null=True, blank=True)
    references = models.TextField(null=True, blank=True)

    marketer_name = models.CharField(max_length=255, null=True, blank=True)
    marketer_address = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Details for {self.medicine.name}"




# APPOLO PHARMACY MEDICINE COUPON GENERATION

class MedicineCoupon(BaseModel):
    COUPON_TYPE = (
        ("self", "Self"),
        ("dependent", "Dependent"),
    )

    vendor = models.ForeignKey(
        PharmacyVendor, on_delete=models.SET_NULL, null=True, related_name="medicine_coupons"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    coupon_name = models.CharField(max_length=255)
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE)
    coupon_code = models.CharField(max_length=20, unique=True)

    # Common fields
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    medicine_name = models.CharField(max_length=255)

    # Dependent Only
    relationship = models.CharField(max_length=50, null=True, blank=True)

    # Optional document
    document = models.FileField(upload_to="medicine_coupons/", null=True, blank=True)
    ordered_date = models.DateField(auto_now_add=True)
    order_type = models.CharField(max_length = 64 , choices =(('home_delivery' , 'Home Delivery') , ('store_pickup' , 'Store Pickup')))
    status = models.CharField(max_length =50)

    def __str__(self):
        return f"#{self.coupon_code} - {self.name}"
    



class PharmacyOrder(models.Model):
    order_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=255)
    order_type = models.CharField(max_length = 64 , choices =(('home_delivery' , 'Home Delivery') , ('store_pickup' , 'Store Pickup')))
    status = models.CharField(max_length=50)
    ordered_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    total_amount = models . DecimalField(max_digits = 10 , decimal_places = 2 , default =0)
    address = models.ForeignKey("addresses.Address", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    prescription_file = models.FileField(upload_to="pharmacy/prescriptions/", null=True, blank=True)

    # Notification Related

    reminder_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"PharmacyOrder {self.order_id} - {self.patient_name}"

class PharmacyOrderItem(models.Model):
    order = models.ForeignKey(PharmacyOrder, on_delete=models.CASCADE, related_name="items")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    amount=models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def total_amount(self):
        return self.quantity * self.medicine.selling_price
