"""
Unified API views for healthcare service providers.
These views abstract away provider-specific logic and provide a consistent API.
"""

from datetime import datetime, date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from .registry import (
    provider_registry,
    get_consultation_provider,
    get_diagnostics_provider,
)
from .base.consultation import (
    ConsultationType,
    BookingRequest,
    CancellationRequest,
    RescheduleRequest,
)
from .base.exceptions import (
    ProviderException,
    ProviderNotFoundError,
    SlotNotAvailableError,
    BookingFailedError,
)
from .models import ExternalAppointment


# ==================== Provider Info ====================

class ProviderListAPIView(APIView):
    """List all available providers."""

    def get(self, request):
        return Response({
            "providers": provider_registry.get_all_providers_info()
        })


class ProviderHealthCheckAPIView(APIView):
    """Check health of all providers."""

    def get(self, request):
        provider_type = request.query_params.get('type')
        provider_name = request.query_params.get('name')

        if provider_name and provider_type:
            # Check specific provider
            try:
                if provider_type == 'consultation':
                    provider = provider_registry.get_consultation_provider(provider_name)
                elif provider_type == 'diagnostics':
                    provider = provider_registry.get_diagnostics_provider(provider_name)
                elif provider_type == 'pharmacy':
                    provider = provider_registry.get_pharmacy_provider(provider_name)
                else:
                    return Response({"error": "Invalid provider type"}, status=400)

                healthy = provider.health_check()
                return Response({
                    "provider": provider_name,
                    "type": provider_type,
                    "healthy": healthy
                })
            except ProviderNotFoundError as e:
                return Response({"error": str(e)}, status=404)

        # Check all providers
        return Response(provider_registry.health_check_all())


# ==================== Consultation APIs ====================

class ConsultationSpecializationsAPIView(APIView):
    """Get specializations from provider."""

    def get(self, request):
        provider_name = request.query_params.get('provider', 'apollo')

        try:
            provider = get_consultation_provider(provider_name)
            specializations = provider.get_specializations()

            return Response({
                "provider": provider_name,
                "specializations": specializations
            })

        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class ConsultationDoctorsAPIView(APIView):
    """Search doctors from provider."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        provider_name = request.query_params.get('provider', 'apollo')

        try:
            provider = get_consultation_provider(provider_name)

            # Parse filters from query params
            consultation_type = None
            if request.query_params.get('consultation_type'):
                consultation_type = ConsultationType(
                    request.query_params.get('consultation_type')
                )

            doctors = provider.search_doctors(
                specialization_id=request.query_params.get('specialization_id'),
                city_id=request.query_params.get('city_id'),
                hospital_id=request.query_params.get('hospital_id'),
                consultation_type=consultation_type,
                search_query=request.query_params.get('search'),
                page=int(request.query_params.get('page', 1)),
                page_size=int(request.query_params.get('page_size', 20)),
            )

            # Convert to dict for response
            doctors_data = [
                {
                    'id': d.provider_doctor_id,
                    'name': d.name,
                    'specialization': d.specialization,
                    'qualification': d.qualification,
                    'experience_years': d.experience_years,
                    'consultation_fee': d.consultation_fee,
                    'hospital_name': d.hospital_name,
                    'hospital_id': d.hospital_id,
                    'city': d.city,
                    'gender': d.gender,
                    'languages': d.languages,
                    'image_url': d.image_url,
                    'available_modes': [m.value for m in d.available_modes],
                    'provider': d.provider_name,
                }
                for d in doctors
            ]

            return Response({
                "provider": provider_name,
                "count": len(doctors_data),
                "doctors": doctors_data
            })

        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class ConsultationDoctorDetailAPIView(APIView):
    """Get doctor details from provider."""
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        provider_name = request.query_params.get('provider', 'apollo')

        try:
            provider = get_consultation_provider(provider_name)
            doctor = provider.get_doctor_details(doctor_id)

            return Response({
                "provider": provider_name,
                "doctor": {
                    'id': doctor.provider_doctor_id,
                    'name': doctor.name,
                    'specialization': doctor.specialization,
                    'qualification': doctor.qualification,
                    'experience_years': doctor.experience_years,
                    'consultation_fee': doctor.consultation_fee,
                    'hospital_name': doctor.hospital_name,
                    'hospital_id': doctor.hospital_id,
                    'city': doctor.city,
                    'gender': doctor.gender,
                    'languages': doctor.languages,
                    'image_url': doctor.image_url,
                    'available_modes': [m.value for m in doctor.available_modes],
                    'provider': doctor.provider_name,
                }
            })

        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class ConsultationAvailabilityAPIView(APIView):
    """Get doctor availability/slots from provider."""
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        provider_name = request.query_params.get('provider', 'apollo')
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({"error": "date is required"}, status=400)

        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        try:
            provider = get_consultation_provider(provider_name)

            consultation_type = None
            if request.query_params.get('consultation_type'):
                consultation_type = ConsultationType(
                    request.query_params.get('consultation_type')
                )

            availability = provider.get_doctor_availability(
                doctor_id=doctor_id,
                date=appointment_date,
                consultation_type=consultation_type,
                hospital_id=request.query_params.get('hospital_id'),
            )

            slots_data = [
                {
                    'slot_id': s.slot_id,
                    'start_time': s.start_time.strftime("%H:%M"),
                    'end_time': s.end_time.strftime("%H:%M"),
                    'is_available': s.is_available,
                    'capacity': s.capacity,
                    'booked_count': s.booked_count,
                    'consultation_type': s.consultation_type.value,
                }
                for s in availability.slots
            ]

            return Response({
                "provider": provider_name,
                "doctor_id": doctor_id,
                "date": date_str,
                "slots": slots_data
            })

        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class ConsultationBookAPIView(APIView):
    """Book a consultation appointment."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider_name = request.data.get('provider', 'apollo')
        user = request.user

        # Validate required fields
        required_fields = ['doctor_id', 'appointment_date', 'slot_id', 'slot_time']
        for field in required_fields:
            if not request.data.get(field):
                return Response({"error": f"{field} is required"}, status=400)

        try:
            # Parse date and time
            appointment_date = datetime.strptime(
                request.data['appointment_date'], "%Y-%m-%d"
            ).date()
            slot_time = datetime.strptime(
                request.data['slot_time'], "%H:%M"
            ).time()

            # Consultation type
            consultation_type = ConsultationType.TELE
            if request.data.get('consultation_type'):
                consultation_type = ConsultationType(request.data['consultation_type'])

            # Create booking request
            booking_request = BookingRequest(
                doctor_id=request.data['doctor_id'],
                patient_name=request.data.get('patient_name', user.name or user.email),
                patient_email=request.data.get('patient_email', user.email),
                patient_mobile=request.data.get('patient_mobile', getattr(user, 'phone', '')),
                patient_gender=request.data.get('patient_gender', ''),
                appointment_date=appointment_date,
                slot_id=request.data['slot_id'],
                slot_time=slot_time,
                consultation_type=consultation_type,
                symptoms=request.data.get('symptoms', ''),
                notes=request.data.get('notes', ''),
                hospital_id=request.data.get('hospital_id', ''),
                city_id=request.data.get('city_id', ''),
                user_id=user.id,
                dependant_id=request.data.get('dependant_id'),
            )

            # Book with provider
            provider = get_consultation_provider(provider_name)
            response = provider.book_appointment(booking_request)

            if response.success:
                # Save to local database
                with transaction.atomic():
                    external_appt = ExternalAppointment.objects.create(
                        user=user,
                        provider_name=provider_name,
                        provider_appointment_id=response.provider_appointment_id,
                        provider_booking_id=response.provider_booking_id,
                        appointment_type='consultation',
                        doctor_id=request.data['doctor_id'],
                        doctor_name=response.doctor_name,
                        hospital_name=response.hospital_name,
                        appointment_date=appointment_date,
                        appointment_time=slot_time,
                        consultation_type=consultation_type.value,
                        status=response.status.value,
                        consultation_fee=response.consultation_fee,
                        meeting_link=response.meeting_link,
                        provider_response=response.extra_data,
                    )

                return Response({
                    "success": True,
                    "message": response.message,
                    "appointment": {
                        "id": external_appt.id,
                        "provider_appointment_id": response.provider_appointment_id,
                        "status": response.status.value,
                        "date": appointment_date.strftime("%Y-%m-%d"),
                        "time": slot_time.strftime("%H:%M"),
                        "doctor_name": response.doctor_name,
                        "hospital_name": response.hospital_name,
                        "consultation_fee": response.consultation_fee,
                        "meeting_link": response.meeting_link,
                    }
                }, status=status.HTTP_201_CREATED)

            return Response({
                "success": False,
                "message": response.message
            }, status=400)

        except SlotNotAvailableError as e:
            return Response({
                "error": "slot_not_available",
                "message": str(e)
            }, status=400)
        except BookingFailedError as e:
            return Response({
                "error": "booking_failed",
                "message": str(e)
            }, status=400)
        except ProviderException as e:
            return Response({"error": str(e)}, status=500)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class ConsultationCancelAPIView(APIView):
    """Cancel a consultation appointment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        provider_name = request.data.get('provider', 'apollo')
        reason = request.data.get('reason', '')

        try:
            # Get the external appointment
            external_appt = ExternalAppointment.objects.get(
                id=appointment_id,
                user=request.user
            )

            provider = get_consultation_provider(provider_name)

            cancel_request = CancellationRequest(
                provider_appointment_id=external_appt.provider_appointment_id,
                reason=reason,
            )

            response = provider.cancel_appointment(cancel_request)

            if response.success:
                external_appt.status = 'cancelled'
                external_appt.save()

                return Response({
                    "success": True,
                    "message": response.message
                })

            return Response({
                "success": False,
                "message": response.message
            }, status=400)

        except ExternalAppointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=404)
        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class ConsultationRescheduleAPIView(APIView):
    """Reschedule a consultation appointment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        provider_name = request.data.get('provider', 'apollo')

        required_fields = ['new_date', 'new_slot_id', 'new_slot_time']
        for field in required_fields:
            if not request.data.get(field):
                return Response({"error": f"{field} is required"}, status=400)

        try:
            new_date = datetime.strptime(request.data['new_date'], "%Y-%m-%d").date()
            new_time = datetime.strptime(request.data['new_slot_time'], "%H:%M").time()

            external_appt = ExternalAppointment.objects.get(
                id=appointment_id,
                user=request.user
            )

            provider = get_consultation_provider(provider_name)

            reschedule_request = RescheduleRequest(
                provider_appointment_id=external_appt.provider_appointment_id,
                new_date=new_date,
                new_slot_id=request.data['new_slot_id'],
                new_slot_time=new_time,
                reason=request.data.get('reason', ''),
            )

            response = provider.reschedule_appointment(reschedule_request)

            if response.success:
                external_appt.appointment_date = new_date
                external_appt.appointment_time = new_time
                external_appt.status = 'rescheduled'
                external_appt.save()

                return Response({
                    "success": True,
                    "message": response.message,
                    "new_date": new_date.strftime("%Y-%m-%d"),
                    "new_time": new_time.strftime("%H:%M"),
                })

            return Response({
                "success": False,
                "message": response.message
            }, status=400)

        except ExternalAppointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=404)
        except ProviderException as e:
            return Response({"error": str(e)}, status=500)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class ConsultationCitiesAPIView(APIView):
    """Get cities from provider."""

    def get(self, request):
        provider_name = request.query_params.get('provider', 'apollo')

        try:
            provider = get_consultation_provider(provider_name)
            cities = provider.get_cities(
                state_id=request.query_params.get('state_id')
            )

            return Response({
                "provider": provider_name,
                "cities": cities
            })

        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class ConsultationHospitalsAPIView(APIView):
    """Get hospitals from provider."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        provider_name = request.query_params.get('provider', 'apollo')

        try:
            provider = get_consultation_provider(provider_name)
            hospitals = provider.get_hospitals(
                city_id=request.query_params.get('city_id'),
                specialization_id=request.query_params.get('specialization_id'),
            )

            return Response({
                "provider": provider_name,
                "hospitals": hospitals
            })

        except ProviderException as e:
            return Response({"error": str(e)}, status=500)


class UserExternalAppointmentsAPIView(APIView):
    """Get user's appointments from external providers."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        appointments = ExternalAppointment.objects.filter(
            user=request.user
        ).order_by('-appointment_date', '-appointment_time')

        status_filter = request.query_params.get('status')
        if status_filter:
            appointments = appointments.filter(status=status_filter)

        provider_filter = request.query_params.get('provider')
        if provider_filter:
            appointments = appointments.filter(provider_name=provider_filter)

        data = [
            {
                'id': a.id,
                'provider': a.provider_name,
                'provider_appointment_id': a.provider_appointment_id,
                'type': a.appointment_type,
                'doctor_name': a.doctor_name,
                'specialization': a.specialization,
                'hospital_name': a.hospital_name,
                'date': a.appointment_date.strftime("%Y-%m-%d"),
                'time': a.appointment_time.strftime("%H:%M"),
                'consultation_type': a.consultation_type,
                'status': a.status,
                'consultation_fee': float(a.consultation_fee),
                'meeting_link': a.meeting_link,
            }
            for a in appointments
        ]

        return Response({
            "count": len(data),
            "appointments": data
        })
