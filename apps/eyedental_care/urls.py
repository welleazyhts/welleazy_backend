from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EyeDentalServiceViewSet,
    EyeTreatmentViewSet, DentalTreatmentViewSet,
    EyeVendorAddressViewSet, DentalVendorAddressViewSet,
    EyeDentalVoucherViewSet, EyeDentalVoucherAdminViewSet
)

router = DefaultRouter()

# Service Programs (Eye Care / Dental Care categories)
router.register("services", EyeDentalServiceViewSet, basename="services")

# Treatments
router.register("eye-treatments", EyeTreatmentViewSet, basename="eye-treatments")
router.register("dental-treatments", DentalTreatmentViewSet, basename="dental-treatments")

# Vendors
router.register("eye-vendors", EyeVendorAddressViewSet, basename="eye-vendors")
router.register("dental-vendors", DentalVendorAddressViewSet, basename="dental-vendors")

# Customer Vouchers
router.register("vouchers", EyeDentalVoucherViewSet, basename="vouchers")

# Admin Case Management
router.register("admin/cases", EyeDentalVoucherAdminViewSet, basename="admin-cases")

urlpatterns = [
    path('', include(router.urls)),
]
