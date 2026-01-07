from django.urls import path , include
from rest_framework.routers import DefaultRouter

from .views import AddToCartAPIView,  ConfirmCheckoutAPIView, UserCartAPIView, CheckoutCartAPIView, AddPackageToCartAPIView , RemoveCartItemAPIView , ClearCartAPIView
from .views import (
    AvailableLabSlotsAPIView,
    
)

from .views import(
    SelectDoctorAPIView,
    AppointmentToCartAPIView,
    
    DoctorAvailabilityViewSet,
    RescheduleAppointmentAPIView,
    CreateAppointmentVoucherAPIView,
)


router=DefaultRouter()
# router.register("cart", CartViewSet, basename="cart")
router.register("doctor-availability", DoctorAvailabilityViewSet, basename="doctor-availability")


urlpatterns = [
    path("" , include(router.urls)),
    path("add-to-cart/", AddToCartAPIView.as_view(), name="appt-add-to-cart"),
    path('select-doctor/' , SelectDoctorAPIView.as_view() , name="select-doctor-before" ),
    path("add-appointment-to-cart/" , AppointmentToCartAPIView.as_view() , name="doc-appt-add-to-cart"),
    # path("add-dentalappt-to-cart/" , DentalAppointmentToCartAPIView.as_view()),
    # path("add-eyeappt-to-cart/" , EyeAppointmentToCartAPIView.as_view()),
    path("cart/", UserCartAPIView.as_view(), name="user-cart"),
    path("cart/<int:cart_id>/checkout/", CheckoutCartAPIView.as_view(), name="cart-checkout"),
    path("cart/<int:cart_id>/confirm/", ConfirmCheckoutAPIView.as_view(), name="cart-confirm"),
    path("add-package-to-cart/", AddPackageToCartAPIView.as_view(), name="appt-add-package-to-cart"),
    path("cart/item/<int:item_id>/remove/", RemoveCartItemAPIView.as_view(), name="cart-remove-item"),
    path("clear/", ClearCartAPIView.as_view(), name="cart-clear"),
    path("lab/slots/<int:center_id>/<str:date>/", AvailableLabSlotsAPIView.as_view()),
    # path("lab/cart/<int:cart_item_id>/select-slot/", SelectLabSlotAPIView.as_view()),
    # path("lab/cart/<int:cart_item_id>/reschedule/", RescheduleLabSlotAPIView.as_view()),
    path("reschedule/<int:cart_item_id>/",RescheduleAppointmentAPIView.as_view(),name="reschedule-appointment"),
    path("voucher/create/<int:appointment_id>/",CreateAppointmentVoucherAPIView.as_view(),name="create-appointment-voucher"),

]
    







