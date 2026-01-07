from django.urls import path, include
from .views import HealthPackageViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'packages', HealthPackageViewSet, basename='healthpackage')

urlpatterns = [
    path('choices/', HealthPackageViewSet.as_view({'get': 'choices'}), name='package-choices'),
    path('', include(router.urls)),
]
