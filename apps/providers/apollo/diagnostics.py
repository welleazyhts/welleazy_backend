"""
Apollo Hospitals Diagnostics Provider Implementation.

Integrates with Apollo's partner API for:
- Test/Package listing
- Slot management
- Booking (Home Collection & Walk-in)
- Rescheduling and Cancellation
"""

import requests
import logging
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

from ..base.diagnostics import (
    DiagnosticsProvider,
    CollectionType,
    BookingStatus,
    LabTest,
    LabPackage,
    DiagnosticCenter,
    CollectionSlot,
    LabBookingRequest,
    LabBookingResponse,
    LabReport,
)
from ..base.exceptions import (
    ProviderAuthenticationError,
    ProviderAPIError,
    SlotNotAvailableError,
    BookingFailedError,
)


logger = logging.getLogger(__name__)


class ApolloDiagnosticsProvider(DiagnosticsProvider):
    """
    Apollo Hospitals diagnostics provider.

    Uses same authentication as consultation provider.
    """

    provider_name = "apollo"
    provider_display_name = "Apollo Diagnostics"

    TOKEN_CACHE_KEY = "apollo_diagnostics_token"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

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
        self.timeout = self.config.get('timeout', 30)

        self._session = requests.Session()

    # ==================== Authentication ====================

    def authenticate(self) -> bool:
        """Authenticate with Apollo API."""
        cached_token = cache.get(self.TOKEN_CACHE_KEY)
        if cached_token:
            self._token = cached_token
            return True

        try:
            response = self._session.post(
                f"{self.api_base_url}/auth/token",
                json={"mobile": self.username, "password": self.password},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                self._token = data.get('token') or data.get('access_token')
                cache.set(self.TOKEN_CACHE_KEY, self._token, 23 * 60 * 60)
                return True

            raise ProviderAuthenticationError(
                f"Apollo authentication failed",
                provider=self.provider_name
            )
        except requests.RequestException as e:
            raise ProviderAuthenticationError(str(e), provider=self.provider_name)

    def is_authenticated(self) -> bool:
        if self._token:
            return True
        cached = cache.get(self.TOKEN_CACHE_KEY)
        if cached:
            self._token = cached
            return True
        return False

    def _ensure_authenticated(self):
        if not self.is_authenticated():
            self.authenticate()

    def _get_headers(self) -> Dict[str, str]:
        self._ensure_authenticated()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.api_base_url}{endpoint}"
        kwargs['headers'] = self._get_headers()
        kwargs['timeout'] = self.timeout

        response = self._session.request(method, url, **kwargs)

        if response.status_code >= 400:
            raise ProviderAPIError(
                f"Apollo API error: {response.text}",
                provider=self.provider_name,
                status_code=response.status_code
            )

        return response.json()

    # ==================== Test Operations ====================

    def search_tests(
        self,
        query: str = None,
        category: str = None,
        city_id: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[LabTest]:
        """Search for lab tests."""
        params = {"pageNumber": page, "pageSize": page_size}
        if query:
            params["searchString"] = query
        if category:
            params["category"] = category
        if city_id:
            params["cityId"] = city_id
        if self.agreement_id:
            params["agreementId"] = self.agreement_id

        data = self._make_request("GET", "/diagnostics/tests", params=params)
        tests = data.get('data', data.get('tests', []))

        return [self._parse_test(t) for t in tests]

    def get_test_details(self, test_id: str) -> LabTest:
        data = self._make_request("GET", f"/diagnostics/tests/{test_id}")
        return self._parse_test(data.get('data', data))

    def _parse_test(self, data: Dict) -> LabTest:
        return LabTest(
            provider_test_id=str(data.get('testId', data.get('id', ''))),
            name=data.get('testName', data.get('name', '')),
            description=data.get('description', ''),
            price=float(data.get('price', data.get('mrp', 0))),
            discounted_price=float(data.get('discountedPrice', data.get('sellingPrice', 0))),
            sample_type=data.get('sampleType', ''),
            fasting_required=data.get('fastingRequired', False),
            report_time=data.get('reportTime', ''),
            category=data.get('category', ''),
            provider_name=self.provider_name,
        )

    def get_packages(self, category: str = None, city_id: str = None) -> List[LabPackage]:
        params = {}
        if category:
            params["category"] = category
        if city_id:
            params["cityId"] = city_id
        if self.agreement_id:
            params["agreementId"] = self.agreement_id

        data = self._make_request("GET", "/diagnostics/packages", params=params)
        packages = data.get('data', data.get('packages', []))

        return [self._parse_package(p) for p in packages]

    def get_package_details(self, package_id: str) -> LabPackage:
        data = self._make_request("GET", f"/diagnostics/packages/{package_id}")
        return self._parse_package(data.get('data', data))

    def _parse_package(self, data: Dict) -> LabPackage:
        return LabPackage(
            provider_package_id=str(data.get('packageId', data.get('id', ''))),
            name=data.get('packageName', data.get('name', '')),
            description=data.get('description', ''),
            price=float(data.get('price', 0)),
            discounted_price=float(data.get('discountedPrice', 0)),
            test_count=data.get('testCount', 0),
            provider_name=self.provider_name,
        )

    # ==================== Serviceability ====================

    def check_serviceability(
        self,
        pincode: str = None,
        city: str = None,
        latitude: float = None,
        longitude: float = None,
    ) -> bool:
        params = {}
        if pincode:
            params["pincode"] = pincode
        if city:
            params["city"] = city

        try:
            data = self._make_request("GET", "/diagnostics/serviceability", params=params)
            return data.get('serviceable', False)
        except ProviderAPIError:
            return False

    def get_serviceable_cities(self) -> List[Dict[str, Any]]:
        data = self._make_request("GET", "/diagnostics/cities")
        return data.get('data', data.get('cities', []))

    # ==================== Center Operations ====================

    def get_centers(
        self,
        city_id: str = None,
        pincode: str = None,
        latitude: float = None,
        longitude: float = None,
    ) -> List[DiagnosticCenter]:
        params = {}
        if city_id:
            params["cityId"] = city_id
        if pincode:
            params["pincode"] = pincode

        data = self._make_request("GET", "/diagnostics/centers", params=params)
        centers = data.get('data', data.get('centers', []))

        return [
            DiagnosticCenter(
                provider_center_id=str(c.get('centerId', c.get('id', ''))),
                name=c.get('centerName', c.get('name', '')),
                address=c.get('address', ''),
                city=c.get('city', ''),
                pincode=c.get('pincode', ''),
                provider_name=self.provider_name,
            )
            for c in centers
        ]

    def get_center_details(self, center_id: str) -> DiagnosticCenter:
        data = self._make_request("GET", f"/diagnostics/centers/{center_id}")
        c = data.get('data', data)
        return DiagnosticCenter(
            provider_center_id=str(c.get('centerId', c.get('id', ''))),
            name=c.get('centerName', c.get('name', '')),
            address=c.get('address', ''),
            city=c.get('city', ''),
            provider_name=self.provider_name,
        )

    # ==================== Slot Operations ====================

    def get_collection_slots(
        self,
        date: date,
        pincode: str = None,
        center_id: str = None,
        collection_type: CollectionType = None,
    ) -> List[CollectionSlot]:
        params = {"date": date.strftime("%Y-%m-%d")}
        if pincode:
            params["pincode"] = pincode
        if center_id:
            params["centerId"] = center_id

        data = self._make_request("GET", "/diagnostics/slots", params=params)
        slots = data.get('data', data.get('slots', []))

        result = []
        for s in slots:
            try:
                start = datetime.strptime(s.get('startTime', ''), "%H:%M").time()
                end = datetime.strptime(s.get('endTime', ''), "%H:%M").time()
            except ValueError:
                continue

            result.append(CollectionSlot(
                slot_id=str(s.get('slotId', '')),
                date=date,
                start_time=start,
                end_time=end,
                is_available=s.get('available', True),
                capacity=s.get('capacity', 1),
            ))

        return result

    # ==================== Booking Operations ====================

    def create_booking(self, request: LabBookingRequest) -> LabBookingResponse:
        payload = {
            "patientName": request.patient_name,
            "email": request.patient_email,
            "mobile": request.patient_mobile,
            "gender": request.patient_gender,
            "age": request.patient_age,
            "address": request.address,
            "city": request.city,
            "pincode": request.pincode,
            "testIds": request.test_ids,
            "packageIds": request.package_ids,
            "centerId": request.center_id,
            "slotId": request.slot_id,
            "slotDate": request.slot_date.strftime("%Y-%m-%d") if request.slot_date else "",
            "collectionType": request.collection_type.value,
            "paymentMode": request.payment_mode,
        }

        if self.agreement_id:
            payload["agreementId"] = self.agreement_id
        if self.client_id:
            payload["clientId"] = self.client_id

        try:
            data = self._make_request("POST", "/diagnostics/book", json=payload)

            return LabBookingResponse(
                success=True,
                provider_booking_id=str(data.get('bookingId', data.get('orderId', ''))),
                status=BookingStatus.CONFIRMED,
                message=data.get('message', 'Booking confirmed'),
                booking_date=request.slot_date,
                total_amount=float(data.get('totalAmount', 0)),
            )
        except ProviderAPIError as e:
            raise BookingFailedError(str(e), provider=self.provider_name)

    def get_booking_status(self, booking_id: str) -> LabBookingResponse:
        data = self._make_request("GET", f"/diagnostics/bookings/{booking_id}")

        status_map = {
            'pending': BookingStatus.PENDING,
            'confirmed': BookingStatus.CONFIRMED,
            'sample_collected': BookingStatus.SAMPLE_COLLECTED,
            'completed': BookingStatus.COMPLETED,
            'cancelled': BookingStatus.CANCELLED,
        }

        return LabBookingResponse(
            success=True,
            provider_booking_id=booking_id,
            status=status_map.get(data.get('status', '').lower(), BookingStatus.PENDING),
        )

    def cancel_booking(self, booking_id: str, reason: str = "") -> LabBookingResponse:
        data = self._make_request(
            "POST",
            f"/diagnostics/bookings/{booking_id}/cancel",
            json={"reason": reason}
        )

        return LabBookingResponse(
            success=True,
            provider_booking_id=booking_id,
            status=BookingStatus.CANCELLED,
            message=data.get('message', 'Booking cancelled'),
        )

    def reschedule_booking(
        self,
        booking_id: str,
        new_date: date,
        new_slot_id: str,
    ) -> LabBookingResponse:
        data = self._make_request(
            "POST",
            f"/diagnostics/bookings/{booking_id}/reschedule",
            json={
                "newDate": new_date.strftime("%Y-%m-%d"),
                "slotId": new_slot_id,
            }
        )

        return LabBookingResponse(
            success=True,
            provider_booking_id=booking_id,
            status=BookingStatus.CONFIRMED,
            booking_date=new_date,
            message=data.get('message', 'Booking rescheduled'),
        )

    # ==================== Report Operations ====================

    def get_reports(self, booking_id: str) -> List[LabReport]:
        data = self._make_request("GET", f"/diagnostics/bookings/{booking_id}/reports")
        reports = data.get('data', data.get('reports', []))

        return [
            LabReport(
                report_id=str(r.get('reportId', '')),
                booking_id=booking_id,
                patient_name=r.get('patientName', ''),
                test_name=r.get('testName', ''),
                report_url=r.get('reportUrl', ''),
                status=r.get('status', ''),
                provider_name=self.provider_name,
            )
            for r in reports
        ]

    def get_report_pdf(self, report_id: str) -> bytes:
        response = self._session.get(
            f"{self.api_base_url}/diagnostics/reports/{report_id}/download",
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return response.content
