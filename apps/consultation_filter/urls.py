

from django.urls import path,include
from apps.location.views import CityViewSet
from rest_framework.routers import DefaultRouter
from .views import DoctorSpecializationViewSet
from .views import LanguageViewSet
from .views import PincodeViewSet
from .views import VendorViewSet
from django.conf.urls.static import static
from django.conf import settings
#DOCTOR SPECIALITY
router = DefaultRouter()
router.register(r'doctor-specializations', DoctorSpecializationViewSet, basename='doctor_specializations')
#LANGUAGES
router.register(r'languages', LanguageViewSet, basename='languages')
#PINCODES
router.register(r'pincodes', PincodeViewSet, basename='pincodes')
#DOCTOR NAMES
# router.register(r'doctors', DoctorViewSet, basename='doctor')
#VENDOR LIST
router.register(r'vendors', VendorViewSet, basename='vendor')
# DOCTOR PERSONAL DETAILS
# router.register(r'doctor-details', DoctorPersonalDetailsViewSet, basename='doctor-details')
urlpatterns = [
    path('', include(router.urls)),
    path('cities/', CityViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('cities/<str:name>/', CityViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)











