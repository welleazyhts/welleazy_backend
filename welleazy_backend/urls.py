"""
URL configuration for welleazy_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/contact/', include('apps.contact.urls')),
    path('api/partner/', include('apps.partner.urls')),
    path('api/location/', include('apps.location.urls')),
    path('api/consultation/',include('apps.consultation_filter.urls')),
    path('api/labtest/', include('apps.labtest.urls')),
    path('api/diagnostic-center/', include('apps.diagnostic_center.urls')),
    path('api/labfilter/', include('apps.labfilter.urls')),
    path('api/dependants/', include('apps.dependants.urls')),
    path('api/addresses/', include('apps.addresses.urls')),
    path('api/doctors_details/',include('apps.doctor_details.urls')),
    path('api/appointments/', include('apps.appointments.urls')),
    path('api/health-packages/', include('apps.health_packages.urls')),
    path('api/sponsored-packages/', include('apps.sponsored_packages.urls')),
    path('api/pharmacy/',include('apps.pharmacy.urls')),
    path('api/health-records/', include('apps.health_records.health.urls')),
    path('api/prescriptions/', include('apps.health_records.prescriptions.urls')),
    path('api/hospitalizations/', include('apps.health_records.hospitalizations.urls')),
    path('api/medical-bills/', include('apps.health_records.medical_bills.urls')),
    path('api/vaccination-certificates/', include('apps.health_records.vaccination_certificates.urls')),
    path('api/medicine-reminders/', include('apps.health_records.medicine_reminders.urls')),
    path('api/health-records/common/', include('apps.health_records.common.urls')),
    path('api/insurance-records/', include('apps.insurance_records.urls')),
    path('api/care-programs/', include('apps.care_programs.urls')),
    path('api/health-assessments/', include('apps.health_assessment.urls')),
    path('api/my-bookings/', include('apps.my_bookings.urls')),
    path('api/' , include ('apps.invoices.urls')),
    path('api/gym_service/' , include('apps.gym_service.urls')),
    path('api/eyedentalcare/',include('apps.eyedental_care.urls')),
    path('api/feedback/' , include('apps.feedback.urls')),
    path('api/women_health/' , include ('apps.women_health.urls')),
    path("api/payments/", include("apps.payments.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/chatbot/", include("apps.chatbot.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)