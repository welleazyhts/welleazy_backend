from django.urls import path

from .views import (
    AddToCartAPIView,
    # UpdateCartItemAPIView,
    RemoveCartItemAPIView,
    IncreaseQuantityAPIView,
    DecreaseQuantityAPIView,
    GetCartAPIView,
    ApplyCouponAPIView,
    RemoveCouponAPIView,
    AddressTypeListAPIView,
    AddressListAPIView,
    SetAddressTypeAPIView,
    SelectAddressForCartAPIView,
    AddNewAddressAPIView,
    UpdateAddressAPIView,
    EstimateDeliveryAPIView,
    UploadPrescriptionAPIView,

    ListPrescriptionsAPIView,
    DownloadPrescriptionAPIView,
    SetDeliveryModeAPIView,
    PharmacyOrderCreateAPIView,
    

)

urlpatterns=[
    path("add/", AddToCartAPIView.as_view()),
    # path("item/<int:item_id>/update/", UpdateCartItemAPIView.as_view()),
    path("item/<int:item_id>/remove/", RemoveCartItemAPIView.as_view()),
    path("increase/", IncreaseQuantityAPIView.as_view()),
    path("decrease/", DecreaseQuantityAPIView.as_view()),
    path("", GetCartAPIView.as_view()),

    # Coupon
    path("coupon/apply/", ApplyCouponAPIView.as_view()),
    path("coupon/remove/", RemoveCouponAPIView.as_view()),

    # Address
    path("addresses/types/", AddressTypeListAPIView.as_view()),
    path("addresses/", AddressListAPIView.as_view()),
    path("addresses/type/select/", SetAddressTypeAPIView.as_view()),
    path("addresses/select/", SelectAddressForCartAPIView.as_view()),
    path("addresses/add/", AddNewAddressAPIView.as_view()),
    path("addresses/update/<int:pk>/", UpdateAddressAPIView.as_view()),
    path("delivery/estimate/", EstimateDeliveryAPIView.as_view()),

    # Prescription
    path("prescription/upload/", UploadPrescriptionAPIView.as_view()),
    path("prescriptions/", ListPrescriptionsAPIView.as_view()),
    path("prescription/download/<int:pk>/", DownloadPrescriptionAPIView.as_view()),
    path("order/create/", PharmacyOrderCreateAPIView.as_view()), 

    # Delivery Mode
    path("delivery_mode/", SetDeliveryModeAPIView.as_view()),
]





