from django.urls import path
from .views import AppointmentInvoiceDetailAPIView, AppointmentInvoicePDFAPIView

urlpatterns = [
    path("appointment/<int:appointment_id>/invoice/", 
         AppointmentInvoiceDetailAPIView.as_view(), name="appointment-invoice-detail"),

    path("appointment/<int:appointment_id>/invoice/pdf/",
         AppointmentInvoicePDFAPIView.as_view(), name="appointment-invoice-pdf"),
]
