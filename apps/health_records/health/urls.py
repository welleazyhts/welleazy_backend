from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HeightRecordViewSet,
    WeightRecordViewSet,
    BmiRecordViewSet,
    BloodPressureRecordViewSet,
    HeartRateRecordViewSet,
    OxygenSaturationRecordViewSet,
    GlucoseRecordViewSet,
    blood_group,
    health_record_choices,
)
router = DefaultRouter()
router.register(r'height', HeightRecordViewSet, basename='height')
router.register(r'weight', WeightRecordViewSet, basename='weight')
router.register(r'bmi', BmiRecordViewSet, basename='bmi')
router.register(r'blood-pressure', BloodPressureRecordViewSet, basename='blood-pressure')
router.register(r'heart-rate', HeartRateRecordViewSet, basename='heart-rate')
router.register(r'oxygen-saturation', OxygenSaturationRecordViewSet, basename='oxygen-saturation')
router.register(r'glucose', GlucoseRecordViewSet, basename='glucose')

urlpatterns = [
    path('', include(router.urls)),
    path('choices/', health_record_choices, name='health_record_choices'),
    path("blood-group/", blood_group, name="blood-group"),
]