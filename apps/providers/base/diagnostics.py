"""
Abstract base class for Diagnostics/Lab Test Service Providers.
Supports: Apollo, Thyrocare, Healthians, Dr. Lal PathLabs, RedCliff, SRL, Orange Health
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class CollectionType(Enum):
    """Types of sample collection."""
    HOME_COLLECTION = "home_collection"
    WALK_IN = "walk_in"
    BOTH = "both"


class BookingStatus(Enum):
    """Status of a lab booking."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SAMPLE_COLLECTED = "sample_collected"
    IN_PROGRESS = "in_progress"
    REPORT_READY = "report_ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


@dataclass
class LabTest:
    """Standardized lab test data from any provider."""
    provider_test_id: str
    name: str
    description: str = ""
    price: float = 0.0
    discounted_price: float = 0.0
    sample_type: str = ""           # Blood, Urine, etc.
    fasting_required: bool = False
    fasting_hours: int = 0
    report_time: str = ""           # e.g., "24-48 hours"
    preparation: str = ""           # Special preparation instructions
    parameters_count: int = 0
    parameters: List[str] = field(default_factory=list)
    category: str = ""
    is_package: bool = False
    provider_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LabPackage:
    """Standardized lab package/profile data."""
    provider_package_id: str
    name: str
    description: str = ""
    price: float = 0.0
    discounted_price: float = 0.0
    tests: List[LabTest] = field(default_factory=list)
    test_count: int = 0
    sample_type: str = ""
    fasting_required: bool = False
    report_time: str = ""
    category: str = ""
    provider_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticCenter:
    """Standardized diagnostic center data."""
    provider_center_id: str
    name: str
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    phone: str = ""
    timing: str = ""
    supports_home_collection: bool = True
    supports_walk_in: bool = True
    provider_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionSlot:
    """Standardized collection time slot."""
    slot_id: str
    date: date
    start_time: time
    end_time: time
    is_available: bool = True
    capacity: int = 1
    booked_count: int = 0
    collection_type: CollectionType = CollectionType.HOME_COLLECTION
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LabBookingRequest:
    """Standardized lab booking request."""
    # Patient details
    patient_name: str
    patient_email: str
    patient_mobile: str
    patient_age: int = 0
    patient_gender: str = ""
    patient_dob: Optional[date] = None

    # Address for home collection
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

    # Booking details
    test_ids: List[str] = field(default_factory=list)
    package_ids: List[str] = field(default_factory=list)
    center_id: str = ""
    collection_type: CollectionType = CollectionType.HOME_COLLECTION
    slot_id: str = ""
    slot_date: date = None
    slot_time: time = None

    # Payment
    payment_mode: str = "prepaid"
    total_amount: float = 0.0

    # Internal references
    user_id: Optional[int] = None
    dependant_id: Optional[int] = None

    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LabBookingResponse:
    """Standardized lab booking response."""
    success: bool
    provider_booking_id: str = ""
    provider_order_id: str = ""
    status: BookingStatus = BookingStatus.PENDING
    message: str = ""
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    collection_address: str = ""
    center_name: str = ""
    total_amount: float = 0.0
    payment_status: str = ""
    estimated_report_date: Optional[date] = None
    phlebotomist_name: str = ""
    phlebotomist_phone: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LabReport:
    """Standardized lab report data."""
    report_id: str
    booking_id: str
    patient_name: str
    test_name: str
    report_date: date = None
    report_url: str = ""            # Download URL
    status: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    provider_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


class DiagnosticsProvider(ABC):
    """
    Abstract base class for diagnostics/lab service providers.

    All diagnostic providers (Apollo, Thyrocare, Healthians, etc.)
    must implement these methods.
    """

    provider_name: str = ""
    provider_display_name: str = ""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._token = None
        self._token_expiry = None

    # ==================== Authentication ====================

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the provider's API."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if current authentication is valid."""
        pass

    # ==================== Test/Package Operations ====================

    @abstractmethod
    def search_tests(
        self,
        query: str = None,
        category: str = None,
        city_id: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[LabTest]:
        """Search for lab tests."""
        pass

    @abstractmethod
    def get_test_details(self, test_id: str) -> LabTest:
        """Get detailed information about a test."""
        pass

    @abstractmethod
    def get_packages(
        self,
        category: str = None,
        city_id: str = None,
    ) -> List[LabPackage]:
        """Get available packages/profiles."""
        pass

    @abstractmethod
    def get_package_details(self, package_id: str) -> LabPackage:
        """Get detailed information about a package."""
        pass

    # ==================== Serviceability ====================

    @abstractmethod
    def check_serviceability(
        self,
        pincode: str = None,
        city: str = None,
        latitude: float = None,
        longitude: float = None,
    ) -> bool:
        """Check if location is serviceable."""
        pass

    @abstractmethod
    def get_serviceable_cities(self) -> List[Dict[str, Any]]:
        """Get list of serviceable cities."""
        pass

    # ==================== Center Operations ====================

    @abstractmethod
    def get_centers(
        self,
        city_id: str = None,
        pincode: str = None,
        latitude: float = None,
        longitude: float = None,
    ) -> List[DiagnosticCenter]:
        """Get nearby diagnostic centers."""
        pass

    @abstractmethod
    def get_center_details(self, center_id: str) -> DiagnosticCenter:
        """Get detailed information about a center."""
        pass

    # ==================== Slot Operations ====================

    @abstractmethod
    def get_collection_slots(
        self,
        date: date,
        pincode: str = None,
        center_id: str = None,
        collection_type: CollectionType = None,
    ) -> List[CollectionSlot]:
        """Get available collection slots for a date."""
        pass

    # ==================== Booking Operations ====================

    @abstractmethod
    def create_booking(self, request: LabBookingRequest) -> LabBookingResponse:
        """Create a lab test booking."""
        pass

    @abstractmethod
    def get_booking_status(self, booking_id: str) -> LabBookingResponse:
        """Get current status of a booking."""
        pass

    @abstractmethod
    def cancel_booking(
        self,
        booking_id: str,
        reason: str = "",
    ) -> LabBookingResponse:
        """Cancel a booking."""
        pass

    @abstractmethod
    def reschedule_booking(
        self,
        booking_id: str,
        new_date: date,
        new_slot_id: str,
    ) -> LabBookingResponse:
        """Reschedule a booking."""
        pass

    # ==================== Report Operations ====================

    @abstractmethod
    def get_reports(self, booking_id: str) -> List[LabReport]:
        """Get reports for a booking."""
        pass

    @abstractmethod
    def get_report_pdf(self, report_id: str) -> bytes:
        """Download report PDF."""
        pass

    # ==================== Utility Methods ====================

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        return {
            'name': self.provider_name,
            'display_name': self.provider_display_name,
            'supports_home_collection': True,
            'supports_walk_in': True,
        }

    def health_check(self) -> bool:
        """Check if provider API is accessible."""
        try:
            return self.authenticate()
        except Exception:
            return False
