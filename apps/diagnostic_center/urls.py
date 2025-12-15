from rest_framework.routers import DefaultRouter
from django.urls import path
from apps.diagnostic_center.views import DiagnosticCenterViewSet, DiagnosticCenterSearchAPIView

router = DefaultRouter()
router.register(r'diagnostic-centers', DiagnosticCenterViewSet, basename='diagnosticcenter')

urlpatterns = [
    path('search/', DiagnosticCenterSearchAPIView.as_view(), name='search-centers'),
]

urlpatterns += router.urls
    