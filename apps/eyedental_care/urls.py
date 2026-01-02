from django.urls import path, include


from rest_framework.routers import DefaultRouter
from .views import (
    EyeTreatmentViewSet, DentalTreatmentViewSet,
    EyeDentalCareBookingViewSet
)

router = DefaultRouter()

router.register("eye-treatments", EyeTreatmentViewSet)
router.register("dental-treatments", DentalTreatmentViewSet)
router.register(
    "",
    EyeDentalCareBookingViewSet,
    basename="eye-dental-care",
)




urlpatterns = [
    path('', include(router.urls)),
]
