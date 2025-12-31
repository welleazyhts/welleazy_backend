from django.urls import path, include
from .views import (
    PharmacyBannerListAPIView,
    PharmacyVendorListAPIView,
    PharmacyCategoryListAPIView,
    PharmacyMedicineFilterAPIView,
)
from .views import (
    CreatePharmacyBannerAPIView,
    UpdatePharmacyBannerAPIView,
    DeletePharmacyBannerAPIView,
   
)
from .views import (
    CreateCategoryAPIView,
    UpdateCategoryAPIView,
    DeleteCategoryAPIView,
)
from .views import (
    CreateVendorAPIView,
    UpdateVendorAPIView,
    DeleteVendorAPIView,
)

from .views import (
    PharmacyMedicineListAPIView,
    MedicineCreateAPIView,
    MedicineUpdateAPIView,
    MedicineDeleteAPIView,
    MedicineDetailAPIView,
    PharmacyMedicineFilterAPIView,
    MedicineDetailsCreateAPIView,
    MedicineDetailsUpdateAPIView,
)

from .views import(
    CreateMedicineCouponAPIView,
    MedicineCouponDetailAPIView,
    CouponListAPIView,
)


urlpatterns = [
    #Banners---
    path("banners/", PharmacyBannerListAPIView.as_view()),
    path("banners/create/", CreatePharmacyBannerAPIView.as_view()),
    path("banners/<int:pk>/update/", UpdatePharmacyBannerAPIView.as_view()),
    path("banners/<int:pk>/delete/", DeletePharmacyBannerAPIView.as_view()),
    # Vendors----
    path("vendors/", PharmacyVendorListAPIView.as_view()),
    path("vendors/create/", CreateVendorAPIView.as_view()),
    path("vendors/<int:pk>/update/", UpdateVendorAPIView.as_view()),
    path("vendors/<int:pk>/delete/", DeleteVendorAPIView.as_view()),
    # Categories----
    path("categories/", PharmacyCategoryListAPIView.as_view()),
    path("categories/create/", CreateCategoryAPIView.as_view()),
    path("categories/<int:pk>/update/", UpdateCategoryAPIView.as_view()),
    path("categories/<int:pk>/delete/", DeleteCategoryAPIView.as_view()),
    
    # Medicines----
    path("medicines/", PharmacyMedicineListAPIView.as_view()),
    path("medicines/create/", MedicineCreateAPIView.as_view()),
    path("medicines/update/<int:pk>/", MedicineUpdateAPIView.as_view()),
    path("medicines/delete/<int:pk>/", MedicineDeleteAPIView.as_view()),
    path("medicines/detail/<str:medicine_name>/", MedicineDetailAPIView.as_view()),
    path("medicines/<medicine_id>/details/" ,MedicineDetailsCreateAPIView.as_view() ),
    path('medicines/<medicine_id>/details/update/' , MedicineDetailsUpdateAPIView.as_view()),

    path("medicines/filter/", PharmacyMedicineFilterAPIView.as_view()),


    # APPOLO COUPON GENERATION---

    
    path("coupons/create/", CreateMedicineCouponAPIView.as_view()),
    path("coupons/<str:coupon_code>/", MedicineCouponDetailAPIView.as_view()),
    path("coupons/", CouponListAPIView.as_view()),




    # Cart URLs will be included here
    path("cart/", include("apps.pharmacy.cart.urls")),

    # Tata 1MG Integration URLs
    path("onemg/", include("apps.pharmacy.onemg_urls")),

]




