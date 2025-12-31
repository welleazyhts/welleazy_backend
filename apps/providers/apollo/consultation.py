"""
Apollo Hospitals Consultation Provider Implementation.

Integrates with Apollo's partner API for:
- Doctor listing and search
- Availability/slot management
- Appointment booking (Tele/Video/In-Clinic)
- Appointment rescheduling and cancellation
"""

import requests
import logging
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

from ..base.consultation import (
    ConsultationProvider,
    ConsultationType,
    AppointmentStatus,
    ProviderDoctor,
    TimeSlot,
    DoctorAvailability,
    BookingRequest,
    BookingResponse,
    CancellationRequest,
    RescheduleRequest,
)
from ..base.exceptions import (
    ProviderAuthenticationError,
    ProviderAPIError,
    SlotNotAvailableError,
    BookingFailedError,
    CancellationFailedError,
    RescheduleFailedError,
)


logger = logging.getLogger(__name__)


class ApolloConsultationProvider(ConsultationProvider):
    """
    Apollo Hospitals consultation provider.

    Configuration required in settings:
        APOLLO_API_BASE_URL = "https://api.apollo247.com"  # or partner API URL
        APOLLO_USERNAME = "your_username"
        APOLLO_PASSWORD = "your_password"
        APOLLO_CLIENT_ID = "your_client_id"
        APOLLO_AGREEMENT_ID = "your_agreement_id"
    """

    provider_name = "apollo"
    provider_display_name = "Apollo Hospitals"

    # Cache keys
    TOKEN_CACHE_KEY = "apollo_consultation_token"
    SPECIALIZATIONS_CACHE_KEY = "apollo_specializations"
    CITIES_CACHE_KEY = "apollo_cities"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        # Load configuration
        self.api_base_url = self.config.get(
            'api_base_url',
            getattr(settings, 'APOLLO_API_BASE_URL', 'https://api.apollo247.com')
        )
        self.username = self.config.get(
            'username',
            getattr(settings, 'APOLLO_USERNAME', '')
        )
        self.password = self.config.get(
            'password',
            getattr(settings, 'APOLLO_PASSWORD', '')
        )
        self.client_id = self.config.get(
            'client_id',
            getattr(settings, 'APOLLO_CLIENT_ID', '')
        )
        self.agreement_id = self.config.get(
            'agreement_id',
            getattr(settings, 'APOLLO_AGREEMENT_ID', '')
        )
        self.timeout = self.config.get(
            'timeout',
            getattr(settings, 'APOLLO_API_TIMEOUT', 30)
        )

        # Session for connection pooling
        self._session = requests.Session()

    # ==================== Authentication ====================

    def authenticate(self) -> bool:
        """Authenticate with Apollo API and get token."""
        # Check cache first
        cached_token = cache.get(self.TOKEN_CACHE_KEY)
        if cached_token:
            self._token = cached_token
            return True

        try:
            response = self._session.post(
                f"{self.api_base_url}/auth/token",
                json={
                    "mobile": self.username,
                    "password": self.password,
                },
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                self._token = data.get('token') or data.get('access_token')

                # Cache token for 23 hours (assuming 24-hour expiry)
                cache.set(self.TOKEN_CACHE_KEY, self._token, 23 * 60 * 60)
                return True

            raise ProviderAuthenticationError(
                f"Apollo authentication failed: {response.text}",
                provider=self.provider_name
            )

        except requests.RequestException as e:
            logger.error(f"Apollo authentication error: {e}")
            raise ProviderAuthenticationError(
                f"Apollo authentication failed: {str(e)}",
                provider=self.provider_name
            )

    def is_authenticated(self) -> bool:
        """Check if current authentication is valid."""
        if self._token:
            return True
        cached_token = cache.get(self.TOKEN_CACHE_KEY)
        if cached_token:
            self._token = cached_token
            return True
        return False

    def _ensure_authenticated(self):
        """Ensure we have a valid token."""
        if not self.is_authenticated():
            self.authenticate()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        self._ensure_authenticated()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Dict[str, Any]:
        """Make API request with error handling."""
        url = f"{self.api_base_url}{endpoint}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )

            if response.status_code == 401:
                # Token expired, re-authenticate and retry
                cache.delete(self.TOKEN_CACHE_KEY)
                self._token = None
                self.authenticate()

                response = self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                )

            if response.status_code >= 400:
                raise ProviderAPIError(
                    f"Apollo API error: {response.text}",
                    provider=self.provider_name,
                    status_code=response.status_code,
                    response_data=response.json() if response.text else {}
                )

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Apollo API request error: {e}")
            raise ProviderAPIError(
                f"Apollo API request failed: {str(e)}",
                provider=self.provider_name
            )

    # ==================== Doctor Operations ====================

    def get_specializations(self) -> List[Dict[str, Any]]:
        """Get list of available specializations."""
        # Check cache
        cached = cache.get(self.SPECIALIZATIONS_CACHE_KEY)
        if cached:
            return cached

        data = self._make_request("GET", "/specializations")
        specializations = data.get('data', data.get('specializations', []))

        # Normalize format
        result = [
            {
                'id': str(s.get('specialityId', s.get('id'))),
                'name': s.get('specialityName', s.get('name', '')),
                'icon': s.get('icon', ''),
            }
            for s in specializations
        ]

        # Cache for 24 hours
        cache.set(self.SPECIALIZATIONS_CACHE_KEY, result, 24 * 60 * 60)
        return result

    def search_doctors(
        self,
        specialization_id: str = None,
        city_id: str = None,
        hospital_id: str = None,
        consultation_type: ConsultationType = None,
        search_query: str = None,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> List[ProviderDoctor]:
        """Search for doctors with filters."""
        params = {
            "pageNumber": page,
            "pageSize": page_size,
        }

        if specialization_id:
            params["specialityId"] = specialization_id
        if city_id:
            params["cityId"] = city_id
        if hospital_id:
            params["hospitalId"] = hospital_id
        if search_query:
            params["searchString"] = search_query
        if consultation_type:
            if consultation_type == ConsultationType.TELE:
                params["consultationType"] = "tele"
            elif consultation_type == ConsultationType.VIDEO:
                params["consultationType"] = "video"
            elif consultation_type == ConsultationType.IN_CLINIC:
                params["hospitalType"] = "clinic"

        # Add agreement/client ID
        if self.agreement_id:
            params["agreementId"] = self.agreement_id
        if self.client_id:
            params["clientId"] = self.client_id

        # Add any additional filters
        params.update(filters)

        data = self._make_request("GET", "/doctors", params=params)
        doctors_data = data.get('data', data.get('doctors', []))

        return [self._parse_doctor(d) for d in doctors_data]

    def get_doctor_details(self, doctor_id: str) -> ProviderDoctor:
        """Get detailed information about a specific doctor."""
        params = {"doctorId": doctor_id}
        if self.client_id:
            params["clientId"] = self.client_id

        data = self._make_request("GET", f"/doctors/{doctor_id}", params=params)
        doctor_data = data.get('data', data)
        return self._parse_doctor(doctor_data)

    def _parse_doctor(self, data: Dict) -> ProviderDoctor:
        """Parse Apollo doctor data into standardized format."""
        # Determine available modes
        available_modes = []
        if data.get('isTeleConsultAvailable') or data.get('teleConsultation'):
            available_modes.append(ConsultationType.TELE)
        if data.get('isVideoConsultAvailable') or data.get('videoConsultation'):
            available_modes.append(ConsultationType.VIDEO)
        if data.get('isClinicVisitAvailable') or data.get('inClinic'):
            available_modes.append(ConsultationType.IN_CLINIC)

        return ProviderDoctor(
            provider_doctor_id=str(data.get('doctorId', data.get('id', ''))),
            name=data.get('doctorName', data.get('name', '')),
            specialization=data.get('speciality', data.get('specialization', '')),
            qualification=data.get('qualification', ''),
            experience_years=int(data.get('experience', 0)),
            consultation_fee=float(data.get('consultationFee', data.get('fee', 0))),
            hospital_name=data.get('hospitalName', data.get('hospital', '')),
            hospital_id=str(data.get('hospitalId', '')),
            city=data.get('city', ''),
            gender=data.get('gender', ''),
            languages=data.get('languages', []),
            image_url=data.get('photoUrl', data.get('image', '')),
            rating=float(data.get('rating', 0)),
            available_modes=available_modes,
            provider_name=self.provider_name,
            extra_data={
                'apollo_doctor_id': data.get('doctorId'),
                'uhid': data.get('uhid'),
            }
        )

    # ==================== Availability Operations ====================

    def get_doctor_availability(
        self,
        doctor_id: str,
        date: date,
        consultation_type: ConsultationType = None,
        hospital_id: str = None,
    ) -> DoctorAvailability:
        """Get available slots for a doctor on a specific date."""
        params = {
            "doctorId": doctor_id,
            "appointmentDate": date.strftime("%Y-%m-%d"),
        }

        if hospital_id:
            params["hospitalId"] = hospital_id
        if consultation_type:
            if consultation_type == ConsultationType.TELE:
                params["consultationType"] = "tele"
            elif consultation_type == ConsultationType.VIDEO:
                params["consultationType"] = "video"

        data = self._make_request("GET", "/slots", params=params)
        slots_data = data.get('data', data.get('slots', []))

        slots = []
        for slot in slots_data:
            slot_time = slot.get('slotTime', '')
            try:
                start_time = datetime.strptime(slot_time, "%H:%M").time()
                # Assume 15-minute slots
                end_dt = datetime.combine(date, start_time) + timedelta(minutes=15)
                end_time = end_dt.time()
            except ValueError:
                continue

            slots.append(TimeSlot(
                slot_id=str(slot.get('slotId', '')),
                start_time=start_time,
                end_time=end_time,
                is_available=slot.get('slotCapacity', 1) > slot.get('bookedSlotCapacity', 0),
                capacity=slot.get('slotCapacity', 1),
                booked_count=slot.get('bookedSlotCapacity', 0),
                consultation_type=consultation_type or ConsultationType.TELE,
            ))

        return DoctorAvailability(
            doctor_id=doctor_id,
            date=date,
            slots=slots,
            provider_name=self.provider_name,
        )

    def get_doctor_availability_range(
        self,
        doctor_id: str,
        start_date: date,
        end_date: date,
        consultation_type: ConsultationType = None,
    ) -> List[DoctorAvailability]:
        """Get availability for a date range."""
        result = []
        current = start_date
        while current <= end_date:
            availability = self.get_doctor_availability(
                doctor_id=doctor_id,
                date=current,
                consultation_type=consultation_type,
            )
            if availability.slots:  # Only include dates with slots
                result.append(availability)
            current += timedelta(days=1)
        return result

    # ==================== Booking Operations ====================

    def book_appointment(self, request: BookingRequest) -> BookingResponse:
        """Book a consultation appointment."""
        # Map consultation type
        consultation_type_value = 1  # Default: tele
        if request.consultation_type == ConsultationType.VIDEO:
            consultation_type_value = 2
        elif request.consultation_type == ConsultationType.IN_CLINIC:
            consultation_type_value = 3

        payload = {
            "firstName": request.patient_name.split()[0] if request.patient_name else "",
            "lastName": " ".join(request.patient_name.split()[1:]) if request.patient_name and len(request.patient_name.split()) > 1 else "",
            "email": request.patient_email,
            "mobile": request.patient_mobile,
            "gender": request.patient_gender,
            "dob": request.patient_dob.strftime("%Y-%m-%d") if request.patient_dob else "",
            "doctorId": int(request.doctor_id),
            "hospitalId": int(request.hospital_id) if request.hospital_id else 0,
            "cityId": int(request.city_id) if request.city_id else 0,
            "appointmentDate": request.appointment_date.strftime("%Y-%m-%d"),
            "slotId": int(request.slot_id),
            "slotTime": request.slot_time.strftime("%H:%M") if request.slot_time else "",
            "consultationType": consultation_type_value,
            "consultationFee": 0,  # Usually handled by agreement
            "paymentMode": "credit",  # Using corporate credit
            "source": "welleazy",
            "bookingSource": "partner_api",
            "comments": request.symptoms or request.notes,
        }

        # Add agreement/client ID
        if self.agreement_id:
            payload["agreementId"] = int(self.agreement_id)
        if self.client_id:
            payload["clientId"] = self.client_id

        try:
            data = self._make_request("POST", "/appointments/book", data=payload)

            return BookingResponse(
                success=True,
                provider_appointment_id=str(data.get('appointmentId', '')),
                provider_booking_id=str(data.get('bookingId', data.get('orderId', ''))),
                status=AppointmentStatus.CONFIRMED,
                message=data.get('message', 'Appointment booked successfully'),
                appointment_date=request.appointment_date,
                appointment_time=request.slot_time,
                doctor_name=data.get('doctorName', ''),
                hospital_name=data.get('hospitalName', ''),
                consultation_fee=float(data.get('consultationFee', 0)),
                meeting_link=data.get('meetingLink', ''),
                extra_data=data,
            )

        except ProviderAPIError as e:
            if "slot" in str(e).lower() or "not available" in str(e).lower():
                raise SlotNotAvailableError(
                    "Selected slot is no longer available",
                    provider=self.provider_name
                )
            raise BookingFailedError(
                f"Booking failed: {str(e)}",
                provider=self.provider_name
            )

    def get_appointment_status(self, provider_appointment_id: str) -> BookingResponse:
        """Get current status of an appointment."""
        data = self._make_request(
            "GET",
            f"/appointments/{provider_appointment_id}"
        )

        status_map = {
            'pending': AppointmentStatus.PENDING,
            'confirmed': AppointmentStatus.CONFIRMED,
            'completed': AppointmentStatus.COMPLETED,
            'cancelled': AppointmentStatus.CANCELLED,
            'no_show': AppointmentStatus.NO_SHOW,
        }

        return BookingResponse(
            success=True,
            provider_appointment_id=provider_appointment_id,
            status=status_map.get(
                data.get('status', '').lower(),
                AppointmentStatus.PENDING
            ),
            message=data.get('message', ''),
            extra_data=data,
        )

    def cancel_appointment(self, request: CancellationRequest) -> BookingResponse:
        """Cancel an appointment."""
        payload = {
            "appointmentId": request.provider_appointment_id,
            "comments": request.reason,
        }

        try:
            data = self._make_request(
                "POST",
                "/appointments/cancel",
                data=payload
            )

            return BookingResponse(
                success=True,
                provider_appointment_id=request.provider_appointment_id,
                status=AppointmentStatus.CANCELLED,
                message=data.get('message', 'Appointment cancelled successfully'),
                extra_data=data,
            )

        except ProviderAPIError as e:
            raise CancellationFailedError(
                f"Cancellation failed: {str(e)}",
                provider=self.provider_name
            )

    def reschedule_appointment(self, request: RescheduleRequest) -> BookingResponse:
        """Reschedule an appointment."""
        payload = {
            "appointmentId": request.provider_appointment_id,
            "appointmentDate": request.new_date.strftime("%Y-%m-%d"),
            "slotId": request.new_slot_id,
            "slotTime": request.new_slot_time.strftime("%H:%M"),
        }

        try:
            data = self._make_request(
                "POST",
                "/appointments/reschedule",
                data=payload
            )

            return BookingResponse(
                success=True,
                provider_appointment_id=request.provider_appointment_id,
                status=AppointmentStatus.RESCHEDULED,
                message=data.get('message', 'Appointment rescheduled successfully'),
                appointment_date=request.new_date,
                appointment_time=request.new_slot_time,
                extra_data=data,
            )

        except ProviderAPIError as e:
            raise RescheduleFailedError(
                f"Reschedule failed: {str(e)}",
                provider=self.provider_name
            )

    # ==================== Location Operations ====================

    def get_cities(self, state_id: str = None) -> List[Dict[str, Any]]:
        """Get list of serviceable cities."""
        cached = cache.get(self.CITIES_CACHE_KEY)
        if cached:
            return cached

        params = {}
        if state_id:
            params["stateId"] = state_id

        data = self._make_request("GET", "/cities", params=params)
        cities = data.get('data', data.get('cities', []))

        result = [
            {
                'id': str(c.get('cityId', c.get('id'))),
                'name': c.get('cityName', c.get('name', '')),
                'state': c.get('stateName', c.get('state', '')),
            }
            for c in cities
        ]

        cache.set(self.CITIES_CACHE_KEY, result, 24 * 60 * 60)
        return result

    def get_hospitals(
        self,
        city_id: str = None,
        specialization_id: str = None,
    ) -> List[Dict[str, Any]]:
        """Get list of hospitals/clinics."""
        params = {}
        if city_id:
            params["cityId"] = city_id
        if specialization_id:
            params["specialityId"] = specialization_id

        data = self._make_request("GET", "/hospitals", params=params)
        hospitals = data.get('data', data.get('hospitals', []))

        return [
            {
                'id': str(h.get('hospitalId', h.get('id'))),
                'name': h.get('hospitalName', h.get('name', '')),
                'address': h.get('address', ''),
                'city': h.get('cityName', h.get('city', '')),
                'pincode': h.get('pincode', ''),
                'latitude': h.get('latitude'),
                'longitude': h.get('longitude'),
            }
            for h in hospitals
        ]
