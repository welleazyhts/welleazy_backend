"""
Tata 1MG API URL Configuration

All URLs for 1MG integration endpoints.
"""

from django.urls import path
from apps.pharmacy.onemg_views import (
    # Search APIs
    OneMGSearchAPIView,
    OneMGAutocompleteAPIView,
    OneMGDrugDetailsAPIView,

    # Serviceability APIs
    OneMGServiceableCitiesAPIView,
    OneMGCheckInventoryAPIView,

    # Order APIs
    OneMGCreateOrderAPIView,
    OneMGOrderStatusAPIView,
    OneMGCancelOrderAPIView,

    # Webhook
    OneMGWebhookView,

    # Health Check
    OneMGHealthCheckAPIView,
)

app_name = 'onemg'

urlpatterns = [
    # Medicine Search
    path('search/', OneMGSearchAPIView.as_view(), name='search'),
    path('autocomplete/', OneMGAutocompleteAPIView.as_view(), name='autocomplete'),
    path('drug/<str:sku_id>/', OneMGDrugDetailsAPIView.as_view(), name='drug_details'),

    # Serviceability
    path('cities/', OneMGServiceableCitiesAPIView.as_view(), name='serviceable_cities'),
    path('inventory/check/', OneMGCheckInventoryAPIView.as_view(), name='check_inventory'),

    # Orders
    path('order/create/', OneMGCreateOrderAPIView.as_view(), name='create_order'),
    path('order/<str:order_id>/status/', OneMGOrderStatusAPIView.as_view(), name='order_status'),
    path('order/<str:order_id>/cancel/', OneMGCancelOrderAPIView.as_view(), name='cancel_order'),

    # Webhooks (public endpoint, no auth required)
    path('webhook/', OneMGWebhookView.as_view(), name='webhook'),

    # Health Check
    path('health/', OneMGHealthCheckAPIView.as_view(), name='health_check'),
]
