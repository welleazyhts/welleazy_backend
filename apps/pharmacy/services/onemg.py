"""
Tata 1MG API Integration Service

This service handles all interactions with the Tata 1MG Partner API including:
- Medicine search and autocomplete
- Inventory/serviceability check
- Order creation and management
- Order status tracking
- Transaction handling

API Documentation: https://developers.1mg.com/ (Partner Portal)
"""

import requests
import hashlib
import hmac
import json
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class OneMGConfig:
    """Configuration for 1MG API"""
    api_base_url: str
    client_id: str
    client_secret: str
    merchant_id: str
    webhook_secret: str
    timeout: int = 30


class OneMGException(Exception):
    """Custom exception for 1MG API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class OneMGService:
    """
    Tata 1MG Partner API Integration Service

    Handles medicine search, inventory check, order creation and tracking.
    """

    # API Endpoints
    ENDPOINTS = {
        'autocomplete': '/api/v2/autocomplete',
        'search': '/api/v2/search',
        'drug_static': '/api/v2/drug/static',
        'inventory_check': '/api/v2/inventory/check',
        'serviceable_cities': '/api/v2/serviceable/cities',
        'create_order': '/api/v2/order/create',
        'order_status': '/api/v2/order/status',
        'cancel_order': '/api/v2/order/cancel',
        'transaction_status': '/api/v2/transaction/status',
        'create_transaction': '/api/v2/transaction/create',
    }

    def __init__(self, config: OneMGConfig = None):
        """Initialize the 1MG service with configuration"""
        if config:
            self.config = config
        else:
            self.config = OneMGConfig(
                api_base_url=getattr(settings, 'ONEMG_API_BASE_URL', 'https://api.1mg.com'),
                client_id=getattr(settings, 'ONEMG_CLIENT_ID', ''),
                client_secret=getattr(settings, 'ONEMG_CLIENT_SECRET', ''),
                merchant_id=getattr(settings, 'ONEMG_MERCHANT_ID', ''),
                webhook_secret=getattr(settings, 'ONEMG_WEBHOOK_SECRET', ''),
                timeout=getattr(settings, 'ONEMG_API_TIMEOUT', 30),
            )

        self._validate_config()

    def _validate_config(self):
        """Validate that required configuration is present"""
        if not self.config.client_id or not self.config.client_secret:
            logger.warning("1MG API credentials not configured. Service will operate in mock mode.")

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client-Id': self.config.client_id,
            'X-Client-Secret': self.config.client_secret,
            'X-Merchant-Id': self.config.merchant_id,
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to 1MG API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body for POST/PUT
            params: Query parameters for GET

        Returns:
            API response as dictionary

        Raises:
            OneMGException: If API request fails
        """
        url = f"{self.config.api_base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.config.timeout
            )

            response_data = response.json() if response.content else {}

            if not response.ok:
                logger.error(f"1MG API error: {response.status_code} - {response_data}")
                raise OneMGException(
                    message=response_data.get('message', 'API request failed'),
                    status_code=response.status_code,
                    response_data=response_data
                )

            return response_data

        except requests.exceptions.Timeout:
            logger.error(f"1MG API timeout for {endpoint}")
            raise OneMGException(message="API request timed out", status_code=504)
        except requests.exceptions.RequestException as e:
            logger.error(f"1MG API request error: {str(e)}")
            raise OneMGException(message=f"API request failed: {str(e)}")

    # ============================================
    # Medicine Search APIs
    # ============================================

    def autocomplete_search(
        self,
        query: str,
        city: str = None,
        search_type: str = 'drug',
        per_page: int = 10
    ) -> List[Dict]:
        """
        Search medicines with autocomplete

        Args:
            query: Search query text
            city: City for availability check
            search_type: Type of search ('drug', 'otc', 'all')
            per_page: Results per page

        Returns:
            List of matching medicines
        """
        params = {
            'q': query,
            'type': search_type,
            'per_page': per_page,
        }
        if city:
            params['city'] = city

        # Check cache first
        cache_key = f"onemg_autocomplete_{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        response = self._make_request('GET', self.ENDPOINTS['autocomplete'], params=params)
        results = response.get('data', [])

        # Cache for 5 minutes
        cache.set(cache_key, results, 300)

        return results

    def search_medicines(
        self,
        query: str,
        city: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Full medicine search with pagination

        Args:
            query: Search query
            city: City for availability
            page: Page number
            per_page: Results per page

        Returns:
            Search results with pagination info
        """
        params = {
            'q': query,
            'page': page,
            'per_page': per_page,
        }
        if city:
            params['city'] = city

        return self._make_request('GET', self.ENDPOINTS['search'], params=params)

    def get_drug_details(self, sku_id: str, locale: str = 'en') -> Dict[str, Any]:
        """
        Get detailed information about a drug/medicine

        Args:
            sku_id: 1MG SKU ID
            locale: Language locale

        Returns:
            Drug details including composition, uses, side effects
        """
        cache_key = f"onemg_drug_{sku_id}_{locale}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        params = {
            'sku_id': sku_id,
            'locale': locale,
            'client': self.config.client_id,
        }

        response = self._make_request('GET', self.ENDPOINTS['drug_static'], params=params)

        # Cache drug details for 1 hour
        cache.set(cache_key, response, 3600)

        return response

    # ============================================
    # Serviceability & Inventory APIs
    # ============================================

    def get_serviceable_cities(self) -> List[str]:
        """
        Get list of cities where 1MG delivery is available

        Returns:
            List of serviceable city names
        """
        cache_key = "onemg_serviceable_cities"
        cached = cache.get(cache_key)
        if cached:
            return cached

        response = self._make_request('GET', self.ENDPOINTS['serviceable_cities'])
        cities = response.get('cities', [])

        # Cache for 24 hours
        cache.set(cache_key, cities, 86400)

        return cities

    def check_inventory(
        self,
        sku_items: List[Dict[str, Any]],
        pincode: str,
        user_info: Dict[str, str] = None,
        coupon_code: str = None
    ) -> Dict[str, Any]:
        """
        Check inventory and serviceability for given SKUs

        Args:
            sku_items: List of items with format [{"sku_id": "xxx", "quantity": 1, "deal_id": ["abc"]}]
            pincode: Delivery pincode
            user_info: User details (email, mobile, first_name, last_name)
            coupon_code: Optional coupon code to apply

        Returns:
            Inventory status with pricing and availability
        """
        # Build SKU string (comma-separated sku_id:quantity pairs)
        skus = ','.join([f"{item['sku_id']}:{item.get('quantity', 1)}" for item in sku_items])

        payload = {
            'skus': skus,
            'pincode': pincode,
            'package': sku_items,  # Full item details including deal_id
        }

        if user_info:
            payload['user'] = {
                'email': user_info.get('email', ''),
                'mobile': user_info.get('mobile', ''),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
            }

        if coupon_code:
            payload['coupon_code'] = coupon_code

        return self._make_request('POST', self.ENDPOINTS['inventory_check'], data=payload)

    # ============================================
    # Order Management APIs
    # ============================================

    def create_order(
        self,
        merchant_order_id: str,
        sku_items: List[Dict[str, Any]],
        user_info: Dict[str, str],
        shipping_address: Dict[str, str],
        payment_method: str = 'prepaid',
        payable_amount: float = 0,
        coupon_code: str = None,
        prescription_url: str = None
    ) -> Dict[str, Any]:
        """
        Create order with 1MG

        Args:
            merchant_order_id: Your unique order ID
            sku_items: List of items [{"sku_id": "xxx", "quantity": 1}]
            user_info: User details (email, mobile, first_name, last_name)
            shipping_address: Address (name, street1, street2, pincode, contact_number, type)
            payment_method: 'prepaid' or 'cod'
            payable_amount: Total amount payable
            coupon_code: Optional coupon
            prescription_url: URL to prescription image if required

        Returns:
            Order creation response with 1MG order ID
        """
        skus = ','.join([f"{item['sku_id']}:{item.get('quantity', 1)}" for item in sku_items])

        payload = {
            'merchant_order_id': merchant_order_id,
            'skus': skus,
            'payment_method': payment_method,
            'payable_amount': str(payable_amount),

            # User info
            'email': user_info.get('email', ''),
            'mobile': user_info.get('mobile', ''),
            'first_name': user_info.get('first_name', ''),
            'last_name': user_info.get('last_name', ''),

            # Shipping address
            'name': shipping_address.get('name', ''),
            'street1': shipping_address.get('street1', ''),
            'street2': shipping_address.get('street2', ''),
            'pincode': shipping_address.get('pincode', ''),
            'contact_number': shipping_address.get('contact_number', ''),
            'type': shipping_address.get('type', 'home'),
        }

        if coupon_code:
            payload['coupon_code'] = coupon_code

        if prescription_url:
            payload['url'] = prescription_url

        logger.info(f"Creating 1MG order for merchant_order_id: {merchant_order_id}")

        return self._make_request('POST', self.ENDPOINTS['create_order'], data=payload)

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status from 1MG

        Args:
            order_id: 1MG order ID

        Returns:
            Order status details
        """
        params = {'order_id': order_id}
        return self._make_request('GET', self.ENDPOINTS['order_status'], params=params)

    def cancel_order(
        self,
        order_id: str,
        reason: str,
        agent_id: str = None
    ) -> Dict[str, Any]:
        """
        Cancel order with 1MG

        Args:
            order_id: 1MG order ID
            reason: Cancellation reason
            agent_id: Optional agent ID who initiated cancellation

        Returns:
            Cancellation response
        """
        payload = {
            'order_id': order_id,
            'reason': reason,
            'merchant': self.config.merchant_id,
        }

        if agent_id:
            payload['agent_id'] = agent_id

        logger.info(f"Cancelling 1MG order: {order_id}, reason: {reason}")

        return self._make_request('POST', self.ENDPOINTS['cancel_order'], data=payload)

    # ============================================
    # Transaction APIs
    # ============================================

    def create_transaction(
        self,
        order_id: str,
        amount: float,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create payment transaction for order

        Args:
            order_id: 1MG order ID
            amount: Transaction amount
            user_id: User identifier

        Returns:
            Transaction details
        """
        payload = {
            'order_id': order_id,
            'amount': amount,
            'user_id': user_id,
        }

        return self._make_request('POST', self.ENDPOINTS['create_transaction'], data=payload)

    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction status

        Args:
            transaction_id: 1MG transaction ID

        Returns:
            Transaction status details
        """
        params = {'transaction_id': transaction_id}
        return self._make_request('GET', self.ENDPOINTS['transaction_status'], params=params)

    # ============================================
    # Webhook Verification
    # ============================================

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from 1MG

        Args:
            payload: Raw request body bytes
            signature: Signature from X-1MG-Signature header

        Returns:
            True if signature is valid
        """
        if not self.config.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True

        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    # ============================================
    # Helper Methods
    # ============================================

    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return bool(self.config.client_id and self.config.client_secret)

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on 1MG API connection

        Returns:
            Health check status
        """
        try:
            # Try to get serviceable cities as a simple health check
            cities = self.get_serviceable_cities()
            return {
                'status': 'healthy',
                'serviceable_cities_count': len(cities),
                'configured': self.is_configured(),
            }
        except OneMGException as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'configured': self.is_configured(),
            }


# Singleton instance
_onemg_service = None

def get_onemg_service() -> OneMGService:
    """Get singleton instance of OneMGService"""
    global _onemg_service
    if _onemg_service is None:
        _onemg_service = OneMGService()
    return _onemg_service
