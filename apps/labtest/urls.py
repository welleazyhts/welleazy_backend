from rest_framework.routers import DefaultRouter
from .views import TestViewSet
from django.urls import path


router = DefaultRouter()
router.register(r'tests', TestViewSet, basename='test')

urlpatterns = router.urls