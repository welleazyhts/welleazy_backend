from django.contrib import admin

# Register your models here.
from apps.pharmacy.models import PharmacyOrder , PharmacyOrderItem , MedicineCoupon as PharmacyCoupon
from apps.labtest.models import Test as LabTestBooking
from apps.sponsored_packages.models import SponsoredPackage as SponsoredPackageBooking
from apps.health_packages.models import HealthPackage as HealthPackageBooking
from apps.appointments.models import Appointment


admin.site.register(Appointment)
admin.site.register(PharmacyOrder)
admin.site.register(PharmacyOrderItem)
admin.site.register(PharmacyCoupon)
admin.site.register(LabTestBooking)
admin.site.register(SponsoredPackageBooking)
admin.site.register(HealthPackageBooking)
from django.conf import settings
user=settings.AUTH_USER_MODEL


# Sample data loader
def create_sample_data(user):
    a = Appointment.objects.create(user=user, case_id='WX48089', status='cancelled', patient_name='Hari', appointment_type='Tele Consultation', appointment_date='2025-11-19', appointment_time='11:00:00')
    p = PharmacyOrder.objects.create(user=user, order_id='PHA0109', status='order_cancelled', patient_name='Hari', order_type='home_delivery', ordered_date='2025-11-18', expected_delivery='2025-11-19', total_amount=126.00, address='Bangalore, Karnataka')
    PharmacyOrderItem.objects.create(order=p, medicine_name='1-AL Tablet', quantity=1, amount=126.00)
    pc = PharmacyCoupon.objects.create(user=user, coupon_order_id='PA78', coupon_code='Ha403661', vendor='Apollo', used=False, status='scheduled')
    l = LabTestBooking.objects.create(user=user, booking_id='LT1001', status='completed', patient_name='Hari', booked_date='2025-11-17')
    s = SponsoredPackageBooking.objects.create(user=user, booking_id='SP200', status='completed', patient_name='Hari', package_name='Full Body Checkup')
    h = HealthPackageBooking.objects.create(user=user, booking_id='HP300', status='completed', patient_name='Hari', package_name='Diabetes Panel')


# Example screenshot path
EXAMPLE_SCREENSHOT_PATH = '/mnt/data/4beefc85-051a-42ba-a06b-434b6dc5b111.png'