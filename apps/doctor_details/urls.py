from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorViewSet,DoctorPersonalViewSet,DoctorProfessionalViewSet

router = DefaultRouter()
router.register('doctors', DoctorViewSet, basename='doctor')



router.register("personal", DoctorPersonalViewSet, basename="doctor-personal")
router.register("professional", DoctorProfessionalViewSet,basename="doctor-professional")


urlpatterns = [
    path('', include(router.urls)),
]







