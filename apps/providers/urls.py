"""
URL routes for unified provider APIs.

These endpoints provide a consistent interface regardless of the underlying provider.
"""

from django.urls import path

from .views import (
    # Provider Info
    ProviderListAPIView,
    ProviderHealthCheckAPIView,

    # Consultation
    ConsultationSpecializationsAPIView,
    ConsultationDoctorsAPIView,
    ConsultationDoctorDetailAPIView,
    ConsultationAvailabilityAPIView,
    ConsultationBookAPIView,
    ConsultationCancelAPIView,
    ConsultationRescheduleAPIView,
    ConsultationCitiesAPIView,
    ConsultationHospitalsAPIView,
    UserExternalAppointmentsAPIView,
)


urlpatterns = [
    # ==================== Provider Info ====================
    path('', ProviderListAPIView.as_view(), name='provider-list'),
    path('health/', ProviderHealthCheckAPIView.as_view(), name='provider-health'),

    # ==================== Consultation ====================
    path('consultation/specializations/', ConsultationSpecializationsAPIView.as_view(), name='consultation-specializations'),
    path('consultation/doctors/', ConsultationDoctorsAPIView.as_view(), name='consultation-doctors'),
    path('consultation/doctors/<str:doctor_id>/', ConsultationDoctorDetailAPIView.as_view(), name='consultation-doctor-detail'),
    path('consultation/doctors/<str:doctor_id>/availability/', ConsultationAvailabilityAPIView.as_view(), name='consultation-availability'),
    path('consultation/book/', ConsultationBookAPIView.as_view(), name='consultation-book'),
    path('consultation/appointments/<int:appointment_id>/cancel/', ConsultationCancelAPIView.as_view(), name='consultation-cancel'),
    path('consultation/appointments/<int:appointment_id>/reschedule/', ConsultationRescheduleAPIView.as_view(), name='consultation-reschedule'),
    path('consultation/cities/', ConsultationCitiesAPIView.as_view(), name='consultation-cities'),
    path('consultation/hospitals/', ConsultationHospitalsAPIView.as_view(), name='consultation-hospitals'),

    # ==================== User Appointments ====================
    path('appointments/', UserExternalAppointmentsAPIView.as_view(), name='user-external-appointments'),
]
