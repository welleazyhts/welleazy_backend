from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CorporateViewSet, CorporatePlanViewSet, CorporateEmployeeViewSet,
    CorporateBookingApprovalViewSet, CorporateInvoiceViewSet
)

router = DefaultRouter()
router.register(r'', CorporateViewSet, basename='corporate')
router.register(r'plans', CorporatePlanViewSet, basename='corporate-plan')
router.register(r'employees', CorporateEmployeeViewSet, basename='corporate-employee')
router.register(r'approvals', CorporateBookingApprovalViewSet, basename='corporate-approval')
router.register(r'invoices', CorporateInvoiceViewSet, basename='corporate-invoice')

urlpatterns = [
    path('', include(router.urls)),
]
