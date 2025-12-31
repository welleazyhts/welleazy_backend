"""
Customer-facing Case URLs
API endpoints for customers to view and manage their cases.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import CustomerCaseViewSet, CustomerCaseDocumentViewSet

# Main router for customer cases
router = DefaultRouter()
router.register(r'my-cases', CustomerCaseViewSet, basename='my-case')

# Nested routers for case-related endpoints
cases_router = nested_routers.NestedDefaultRouter(router, r'my-cases', lookup='case')
cases_router.register(r'documents', CustomerCaseDocumentViewSet, basename='case-documents')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(cases_router.urls)),
]
