"""
Abstract base class for Pharmacy Service Providers.
Supports: Tata 1MG, Apollo Pharmacy, and future pharmacy providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class DeliveryType(Enum):
    """Types of delivery."""
    HOME_DELIVERY = "home_delivery"
    STORE_PICKUP = "store_pickup"


class OrderStatus(Enum):
    """Status of a pharmacy order."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


@dataclass
class Medicine:
    """Standardized medicine data from any provider."""
    provider_sku: str               # Provider's SKU/product ID
    name: str
    manufacturer: str = ""
    composition: str = ""           # Salt composition
    mrp: float = 0.0
    selling_price: float = 0.0
    discount_percent: float = 0.0
    pack_size: str = ""             # e.g., "10 tablets", "100ml"
    unit: str = ""
    prescription_required: bool = False
    in_stock: bool = True
    quantity_available: int = 0
    category: str = ""
    drug_type: str = ""             # Tablet, Syrup, Injection, etc.
    image_url: str = ""
    description: str = ""
    side_effects: str = ""
    uses: str = ""
    provider_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PharmacyStore:
    """Standardized pharmacy store data."""
    provider_store_id: str
    name: str
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    phone: str = ""
    timing: str = ""
    supports_delivery: bool = True
    supports_pickup: bool = True
    provider_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CartItem:
    """Item in pharmacy cart."""
    provider_sku: str
    name: str
    quantity: int = 1
    mrp: float = 0.0
    selling_price: float = 0.0
    total_price: float = 0.0
    prescription_required: bool = False


@dataclass
class PharmacyOrderRequest:
    """Standardized pharmacy order request."""
    # Customer details
    customer_name: str
    customer_email: str
    customer_mobile: str

    # Delivery address
    address: str
    city: str
    state: str
    pincode: str
    latitude: float = 0.0
    longitude: float = 0.0

    # Order details
    items: List[CartItem] = field(default_factory=list)
    delivery_type: DeliveryType = DeliveryType.HOME_DELIVERY
    store_id: str = ""              # For store pickup

    # Prescription
    prescription_images: List[str] = field(default_factory=list)
    prescription_ids: List[str] = field(default_factory=list)

    # Payment
    payment_mode: str = "prepaid"   # prepaid/cod
    total_mrp: float = 0.0
    total_discount: float = 0.0
    delivery_charge: float = 0.0
    total_amount: float = 0.0

    # Coupon
    coupon_code: str = ""

    # Internal references
    user_id: Optional[int] = None
    cart_id: Optional[int] = None

    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PharmacyOrderResponse:
    """Standardized pharmacy order response."""
    success: bool
    provider_order_id: str = ""
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    order_date: Optional[datetime] = None
    expected_delivery: Optional[date] = None
    delivery_address: str = ""
    total_amount: float = 0.0
    payment_status: str = ""
    tracking_url: str = ""
    tracking_id: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)


class PharmacyProvider(ABC):
    """
    Abstract base class for pharmacy service providers.

    All pharmacy providers (1MG, Apollo Pharmacy, etc.)
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

    # ==================== Medicine Operations ====================

    @abstractmethod
    def search_medicines(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Medicine]:
        """Search for medicines."""
        pass

    @abstractmethod
    def get_medicine_details(self, sku: str) -> Medicine:
        """Get detailed information about a medicine."""
        pass

    @abstractmethod
    def autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions for medicine search."""
        pass

    # ==================== Inventory Operations ====================

    @abstractmethod
    def check_inventory(
        self,
        sku_list: List[str],
        pincode: str,
    ) -> Dict[str, Any]:
        """Check inventory for multiple SKUs at a location."""
        pass

    @abstractmethod
    def check_serviceability(
        self,
        pincode: str,
    ) -> bool:
        """Check if location is serviceable."""
        pass

    @abstractmethod
    def get_serviceable_cities(self) -> List[Dict[str, Any]]:
        """Get list of serviceable cities."""
        pass

    # ==================== Store Operations ====================

    @abstractmethod
    def get_nearby_stores(
        self,
        pincode: str = None,
        latitude: float = None,
        longitude: float = None,
    ) -> List[PharmacyStore]:
        """Get nearby pharmacy stores."""
        pass

    # ==================== Order Operations ====================

    @abstractmethod
    def create_order(self, request: PharmacyOrderRequest) -> PharmacyOrderResponse:
        """Create a pharmacy order."""
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> PharmacyOrderResponse:
        """Get current status of an order."""
        pass

    @abstractmethod
    def cancel_order(
        self,
        order_id: str,
        reason: str = "",
    ) -> PharmacyOrderResponse:
        """Cancel an order."""
        pass

    # ==================== Coupon Operations ====================

    @abstractmethod
    def validate_coupon(
        self,
        coupon_code: str,
        cart_amount: float,
    ) -> Dict[str, Any]:
        """Validate a coupon code."""
        pass

    @abstractmethod
    def apply_coupon(
        self,
        order_id: str,
        coupon_code: str,
    ) -> Dict[str, Any]:
        """Apply a coupon to an order."""
        pass

    # ==================== Prescription Operations ====================

    @abstractmethod
    def upload_prescription(
        self,
        image_data: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """Upload a prescription image."""
        pass

    # ==================== Utility Methods ====================

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        return {
            'name': self.provider_name,
            'display_name': self.provider_display_name,
            'supports_cod': True,
            'supports_prescription_upload': True,
        }

    def health_check(self) -> bool:
        """Check if provider API is accessible."""
        try:
            return self.authenticate()
        except Exception:
            return False
