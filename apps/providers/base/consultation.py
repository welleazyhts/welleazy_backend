"""
Abstract base class for Consultation Service Providers.
Supports: Apollo, and any future consultation providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ConsultationType(Enum):
    """Types of consultation available."""
    TELE = "tele"           # Phone call consultation
    VIDEO = "video"         # Video call consultation
    IN_CLINIC = "in_clinic" # In-person at clinic
    CHAT = "chat"           # Text chat consultation


class AppointmentStatus(Enum):
    """Status of an appointment."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


@dataclass
class ProviderDoctor:
    """Standardized doctor data from any provider."""
    provider_doctor_id: str          # ID from the provider's system
    name: str
    specialization: str
    qualification: str = ""
    experience_years: int = 0
    consultation_fee: float = 0.0
    hospital_name: str = ""
    hospital_id: str = ""
    city: str = ""
    gender: str = ""
    languages: List[str] = field(default_factory=list)
    image_url: str = ""
    rating: float = 0.0
    available_modes: List[ConsultationType] = field(default_factory=list)
    provider_name: str = ""          # e.g., "apollo", "practo"
    extra_data: Dict[str, Any] = field(default_factory=dict)  # Provider-specific data


@dataclass
class TimeSlot:
    """Standardized time slot data."""
    slot_id: str                     # Provider's slot ID
    start_time: time
    end_time: time
    is_available: bool = True
    capacity: int = 1
    booked_count: int = 0
    consultation_type: ConsultationType = ConsultationType.TELE
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DoctorAvailability:
    """Doctor availability for a specific date."""
    doctor_id: str
    date: date
    slots: List[TimeSlot] = field(default_factory=list)
    provider_name: str = ""


@dataclass
class BookingRequest:
    """Standardized booking request."""
    doctor_id: str
    patient_name: str
    patient_email: str
    patient_mobile: str
    patient_dob: Optional[date] = None
    patient_gender: str = ""
    appointment_date: date = None
    slot_id: str = ""
    slot_time: time = None
    consultation_type: ConsultationType = ConsultationType.TELE
    symptoms: str = ""
    notes: str = ""
    # Internal references
    user_id: Optional[int] = None
    dependant_id: Optional[int] = None
    # Provider-specific
    hospital_id: str = ""
    city_id: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BookingResponse:
    """Standardized booking response."""
    success: bool
    provider_appointment_id: str = ""   # ID from provider's system
    provider_booking_id: str = ""       # Alternative booking reference
    status: AppointmentStatus = AppointmentStatus.PENDING
    message: str = ""
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    doctor_name: str = ""
    hospital_name: str = ""
    consultation_fee: float = 0.0
    payment_status: str = ""
    meeting_link: str = ""              # For video consultations
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CancellationRequest:
    """Standardized cancellation request."""
    provider_appointment_id: str
    reason: str = ""
    cancelled_by: str = "patient"       # patient/doctor/system
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RescheduleRequest:
    """Standardized reschedule request."""
    provider_appointment_id: str
    new_date: date
    new_slot_id: str
    new_slot_time: time
    reason: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


class ConsultationProvider(ABC):
    """
    Abstract base class for consultation service providers.

    All consultation providers (Apollo, Practo, etc.) must implement
    these methods to ensure consistent API across providers.
    """

    # Provider identification
    provider_name: str = ""
    provider_display_name: str = ""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration (API keys, endpoints, etc.)
        """
        self.config = config or {}
        self._token = None
        self._token_expiry = None

    # ==================== Authentication ====================

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the provider's API.

        Returns:
            bool: True if authentication successful

        Raises:
            ProviderAuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if current authentication is valid."""
        pass

    # ==================== Doctor Operations ====================

    @abstractmethod
    def get_specializations(self) -> List[Dict[str, Any]]:
        """
        Get list of available specializations.

        Returns:
            List of specialization dictionaries with 'id' and 'name'
        """
        pass

    @abstractmethod
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
        """
        Search for doctors with filters.

        Returns:
            List of ProviderDoctor objects
        """
        pass

    @abstractmethod
    def get_doctor_details(self, doctor_id: str) -> ProviderDoctor:
        """
        Get detailed information about a specific doctor.

        Returns:
            ProviderDoctor object with full details
        """
        pass

    # ==================== Availability Operations ====================

    @abstractmethod
    def get_doctor_availability(
        self,
        doctor_id: str,
        date: date,
        consultation_type: ConsultationType = None,
        hospital_id: str = None,
    ) -> DoctorAvailability:
        """
        Get available slots for a doctor on a specific date.

        Returns:
            DoctorAvailability with list of TimeSlots
        """
        pass

    @abstractmethod
    def get_doctor_availability_range(
        self,
        doctor_id: str,
        start_date: date,
        end_date: date,
        consultation_type: ConsultationType = None,
    ) -> List[DoctorAvailability]:
        """
        Get availability for a date range.

        Returns:
            List of DoctorAvailability for each date
        """
        pass

    # ==================== Booking Operations ====================

    @abstractmethod
    def book_appointment(self, request: BookingRequest) -> BookingResponse:
        """
        Book a consultation appointment.

        Returns:
            BookingResponse with appointment details

        Raises:
            SlotNotAvailableError: If slot is no longer available
            BookingFailedError: If booking fails
        """
        pass

    @abstractmethod
    def get_appointment_status(self, provider_appointment_id: str) -> BookingResponse:
        """
        Get current status of an appointment.

        Returns:
            BookingResponse with current status
        """
        pass

    @abstractmethod
    def cancel_appointment(self, request: CancellationRequest) -> BookingResponse:
        """
        Cancel an appointment.

        Returns:
            BookingResponse with cancellation status

        Raises:
            CancellationFailedError: If cancellation fails
        """
        pass

    @abstractmethod
    def reschedule_appointment(self, request: RescheduleRequest) -> BookingResponse:
        """
        Reschedule an appointment.

        Returns:
            BookingResponse with new appointment details

        Raises:
            RescheduleFailedError: If reschedule fails
        """
        pass

    # ==================== Location Operations ====================

    @abstractmethod
    def get_cities(self, state_id: str = None) -> List[Dict[str, Any]]:
        """
        Get list of serviceable cities.

        Returns:
            List of city dictionaries with 'id' and 'name'
        """
        pass

    @abstractmethod
    def get_hospitals(
        self,
        city_id: str = None,
        specialization_id: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get list of hospitals/clinics.

        Returns:
            List of hospital dictionaries
        """
        pass

    # ==================== Utility Methods ====================

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        return {
            'name': self.provider_name,
            'display_name': self.provider_display_name,
            'supported_modes': [ct.value for ct in ConsultationType],
        }

    def health_check(self) -> bool:
        """Check if provider API is accessible."""
        try:
            return self.authenticate()
        except Exception:
            return False
