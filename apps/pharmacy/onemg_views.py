"""
Tata 1MG API Views

Views for 1MG integration including:
- Medicine search through 1MG
- Inventory/serviceability check
- Order creation with 1MG
- Webhook handlers for order status updates
"""

import json
import uuid
import logging
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from apps.pharmacy.services.onemg import get_onemg_service, OneMGException
from apps.pharmacy.models import PharmacyOrder, Medicine
from apps.pharmacy.onemg_models import (
    OneMGOrder,
    OneMGOrderItem,
    OneMGWebhookLog,
    OneMGMedicineMapping,
    OneMGServiceableCity,
)
from apps.notifications.utils import notify_user

logger = logging.getLogger(__name__)


# ============================================
# Medicine Search APIs
# ============================================

class OneMGSearchAPIView(APIView):
    """
    Search medicines through Tata 1MG API
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        city = request.query_params.get('city', '')
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))

        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = get_onemg_service()

            if not service.is_configured():
                return Response(
                    {'error': '1MG integration not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            results = service.search_medicines(
                query=query,
                city=city,
                page=page,
                per_page=per_page
            )

            return Response(results)

        except OneMGException as e:
            logger.error(f"1MG search error: {e.message}")
            return Response(
                {'error': e.message},
                status=status.HTTP_502_BAD_GATEWAY
            )


class OneMGAutocompleteAPIView(APIView):
    """
    Autocomplete search for medicines through 1MG
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        city = request.query_params.get('city', '')

        if len(query) < 2:
            return Response({'results': []})

        try:
            service = get_onemg_service()

            if not service.is_configured():
                # Fallback to local search
                medicines = Medicine.objects.filter(
                    name__icontains=query
                )[:10]
                return Response({
                    'results': [
                        {
                            'id': m.id,
                            'name': m.name,
                            'price': float(m.selling_price),
                            'source': 'local'
                        }
                        for m in medicines
                    ]
                })

            results = service.autocomplete_search(
                query=query,
                city=city,
                per_page=10
            )

            return Response({'results': results})

        except OneMGException as e:
            logger.error(f"1MG autocomplete error: {e.message}")
            # Fallback to local
            medicines = Medicine.objects.filter(name__icontains=query)[:10]
            return Response({
                'results': [
                    {
                        'id': m.id,
                        'name': m.name,
                        'price': float(m.selling_price),
                        'source': 'local'
                    }
                    for m in medicines
                ]
            })


class OneMGDrugDetailsAPIView(APIView):
    """
    Get detailed medicine information from 1MG
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, sku_id):
        try:
            service = get_onemg_service()

            if not service.is_configured():
                return Response(
                    {'error': '1MG integration not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            details = service.get_drug_details(sku_id=sku_id)
            return Response(details)

        except OneMGException as e:
            return Response(
                {'error': e.message},
                status=status.HTTP_502_BAD_GATEWAY
            )


# ============================================
# Serviceability & Inventory APIs
# ============================================

class OneMGServiceableCitiesAPIView(APIView):
    """
    Get list of cities where 1MG delivery is available
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = get_onemg_service()

            if not service.is_configured():
                # Return cached cities from database
                cities = OneMGServiceableCity.objects.filter(
                    is_active=True
                ).values_list('city_name', flat=True)
                return Response({'cities': list(cities)})

            cities = service.get_serviceable_cities()

            # Update cache in database
            for city in cities:
                OneMGServiceableCity.objects.update_or_create(
                    city_name=city,
                    defaults={'is_active': True}
                )

            return Response({'cities': cities})

        except OneMGException as e:
            # Return cached cities on error
            cities = OneMGServiceableCity.objects.filter(
                is_active=True
            ).values_list('city_name', flat=True)
            return Response({'cities': list(cities)})


class OneMGCheckInventoryAPIView(APIView):
    """
    Check inventory and serviceability for medicines
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        items = request.data.get('items', [])
        pincode = request.data.get('pincode')
        coupon_code = request.data.get('coupon_code')

        if not items:
            return Response(
                {'error': 'Items are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not pincode:
            return Response(
                {'error': 'Pincode is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = get_onemg_service()

            if not service.is_configured():
                return Response(
                    {'error': '1MG integration not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            user = request.user
            user_info = {
                'email': user.email,
                'mobile': getattr(user, 'phone', ''),
                'first_name': getattr(user, 'first_name', user.email.split('@')[0]),
                'last_name': getattr(user, 'last_name', ''),
            }

            result = service.check_inventory(
                sku_items=items,
                pincode=pincode,
                user_info=user_info,
                coupon_code=coupon_code
            )

            return Response(result)

        except OneMGException as e:
            return Response(
                {'error': e.message},
                status=status.HTTP_502_BAD_GATEWAY
            )


# ============================================
# Order Management APIs
# ============================================

class OneMGCreateOrderAPIView(APIView):
    """
    Create order with 1MG from existing PharmacyOrder
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')

        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pharmacy_order = PharmacyOrder.objects.get(
                order_id=order_id,
                user=request.user
            )
        except PharmacyOrder.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already submitted to 1MG
        if hasattr(pharmacy_order, 'onemg_order'):
            return Response({
                'message': 'Order already submitted to 1MG',
                'onemg_order_id': pharmacy_order.onemg_order.onemg_order_id
            })

        try:
            service = get_onemg_service()

            if not service.is_configured():
                return Response(
                    {'error': '1MG integration not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Build SKU items from order
            sku_items = []
            for item in pharmacy_order.items.all():
                # Try to get 1MG SKU mapping
                try:
                    mapping = OneMGMedicineMapping.objects.get(medicine=item.medicine)
                    sku_items.append({
                        'sku_id': mapping.sku_id,
                        'quantity': item.quantity
                    })
                except OneMGMedicineMapping.DoesNotExist:
                    return Response(
                        {'error': f'Medicine {item.medicine.name} not mapped to 1MG SKU'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # User info
            user = request.user
            user_info = {
                'email': user.email,
                'mobile': getattr(user, 'phone', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
            }

            # Shipping address
            address = pharmacy_order.address
            shipping_address = {
                'name': pharmacy_order.patient_name,
                'street1': address.address_line1 if address else '',
                'street2': address.address_line2 if address else '',
                'pincode': address.pincode if address else '',
                'contact_number': getattr(user, 'phone', ''),
                'type': 'home',
            }

            # Payment method
            payment_method = 'cod' if pharmacy_order.order_type == 'cod' else 'prepaid'

            # Prescription URL (if exists)
            prescription_url = None
            if pharmacy_order.prescription_file:
                prescription_url = request.build_absolute_uri(
                    pharmacy_order.prescription_file.url
                )

            # Create order with 1MG
            result = service.create_order(
                merchant_order_id=pharmacy_order.order_id,
                sku_items=sku_items,
                user_info=user_info,
                shipping_address=shipping_address,
                payment_method=payment_method,
                payable_amount=float(pharmacy_order.total_amount),
                prescription_url=prescription_url
            )

            # Create OneMGOrder record
            onemg_order = OneMGOrder.objects.create(
                pharmacy_order=pharmacy_order,
                onemg_order_id=result.get('order_id', ''),
                onemg_status='confirmed',
                total_amount=pharmacy_order.total_amount,
                last_api_response=result
            )

            # Create order items
            for item in pharmacy_order.items.all():
                try:
                    mapping = OneMGMedicineMapping.objects.get(medicine=item.medicine)
                    OneMGOrderItem.objects.create(
                        onemg_order=onemg_order,
                        sku_id=mapping.sku_id,
                        product_name=item.medicine.name,
                        quantity=item.quantity,
                        selling_price=item.medicine.selling_price,
                        total=item.amount
                    )
                except OneMGMedicineMapping.DoesNotExist:
                    pass

            return Response({
                'message': 'Order submitted to 1MG successfully',
                'onemg_order_id': onemg_order.onemg_order_id,
                'result': result
            }, status=status.HTTP_201_CREATED)

        except OneMGException as e:
            logger.error(f"1MG order creation error: {e.message}")
            return Response(
                {'error': e.message},
                status=status.HTTP_502_BAD_GATEWAY
            )


class OneMGOrderStatusAPIView(APIView):
    """
    Get order status from 1MG
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            onemg_order = OneMGOrder.objects.get(
                pharmacy_order__order_id=order_id,
                pharmacy_order__user=request.user
            )
        except OneMGOrder.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            service = get_onemg_service()

            if service.is_configured():
                # Fetch latest status from 1MG
                result = service.get_order_status(onemg_order.onemg_order_id)

                # Update local record
                onemg_order.onemg_status = result.get('status', onemg_order.onemg_status)
                onemg_order.last_api_response = result
                onemg_order.save()

            return Response({
                'order_id': order_id,
                'onemg_order_id': onemg_order.onemg_order_id,
                'status': onemg_order.onemg_status,
                'tracking_number': onemg_order.tracking_number,
                'tracking_url': onemg_order.tracking_url,
                'courier_name': onemg_order.courier_name,
                'estimated_delivery': onemg_order.estimated_delivery_date,
            })

        except OneMGException as e:
            # Return cached data on error
            return Response({
                'order_id': order_id,
                'onemg_order_id': onemg_order.onemg_order_id,
                'status': onemg_order.onemg_status,
                'tracking_number': onemg_order.tracking_number,
                'error': 'Could not fetch latest status'
            })


class OneMGCancelOrderAPIView(APIView):
    """
    Cancel order with 1MG
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        reason = request.data.get('reason', 'Customer requested cancellation')

        try:
            onemg_order = OneMGOrder.objects.get(
                pharmacy_order__order_id=order_id,
                pharmacy_order__user=request.user
            )
        except OneMGOrder.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if onemg_order.onemg_status in ['delivered', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel order in {onemg_order.onemg_status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = get_onemg_service()

            if not service.is_configured():
                return Response(
                    {'error': '1MG integration not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            result = service.cancel_order(
                order_id=onemg_order.onemg_order_id,
                reason=reason
            )

            # Update local record
            onemg_order.onemg_status = 'cancelled'
            onemg_order.last_api_response = result
            onemg_order.save()

            # Update pharmacy order
            onemg_order.pharmacy_order.status = 'cancelled'
            onemg_order.pharmacy_order.save()

            return Response({
                'message': 'Order cancelled successfully',
                'order_id': order_id
            })

        except OneMGException as e:
            return Response(
                {'error': e.message},
                status=status.HTTP_502_BAD_GATEWAY
            )


# ============================================
# Webhook Handlers
# ============================================

@method_decorator(csrf_exempt, name='dispatch')
class OneMGWebhookView(APIView):
    """
    Handle webhooks from Tata 1MG for order status updates

    All webhooks from 1MG are received here and processed.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def post(self, request):
        # Generate unique event ID
        event_id = str(uuid.uuid4())

        # Get raw body for signature verification
        raw_body = request.body

        # Parse JSON
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in 1MG webhook")
            return Response(
                {'error': 'Invalid JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get signature from header
        signature = request.META.get('HTTP_X_1MG_SIGNATURE', '')

        # Determine event type
        event_type = data.get('event_type', 'unknown')
        onemg_order_id = data.get('order_id', '')

        # Create webhook log
        webhook_log = OneMGWebhookLog.objects.create(
            event_id=event_id,
            event_type=event_type,
            onemg_order_id=onemg_order_id,
            request_headers=dict(request.headers),
            request_body=data,
            signature=signature,
            source_ip=self.get_client_ip(request)
        )

        # Verify signature
        service = get_onemg_service()
        signature_valid = service.verify_webhook_signature(raw_body, signature)
        webhook_log.signature_valid = signature_valid

        if not signature_valid and service.config.webhook_secret:
            webhook_log.processing_status = 'failed'
            webhook_log.error_message = 'Invalid signature'
            webhook_log.save()
            logger.warning(f"Invalid webhook signature for event {event_id}")
            return Response({'status': 'signature_invalid'}, status=status.HTTP_401_UNAUTHORIZED)

        # Process webhook
        try:
            self._process_webhook(webhook_log, data)
            webhook_log.processing_status = 'processed'
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            return Response({'status': 'processed', 'event_id': event_id})

        except Exception as e:
            logger.exception(f"Error processing webhook {event_id}")
            webhook_log.processing_status = 'failed'
            webhook_log.error_message = str(e)
            webhook_log.save()
            return Response({'status': 'error', 'event_id': event_id})

    def _process_webhook(self, webhook_log, data):
        """Process webhook based on event type"""
        event_type = data.get('event_type', '')
        onemg_order_id = data.get('order_id', '')

        if not onemg_order_id:
            logger.warning("No order_id in webhook")
            return

        # Find the order
        try:
            onemg_order = OneMGOrder.objects.get(onemg_order_id=onemg_order_id)
            webhook_log.pharmacy_order = onemg_order.pharmacy_order
        except OneMGOrder.DoesNotExist:
            logger.warning(f"Order not found for webhook: {onemg_order_id}")
            return

        # Process based on event type
        handler_map = {
            'order_confirmed': self._handle_order_confirmed,
            'order_packed': self._handle_order_packed,
            'order_shipped': self._handle_order_shipped,
            'out_for_delivery': self._handle_out_for_delivery,
            'order_delivered': self._handle_order_delivered,
            'order_cancelled': self._handle_order_cancelled,
            'order_stuck': self._handle_order_stuck,
            'prescription_rejected': self._handle_prescription_rejected,
        }

        handler = handler_map.get(event_type)
        if handler:
            handler(onemg_order, data)
        else:
            logger.info(f"Unknown webhook event type: {event_type}")

    def _handle_order_confirmed(self, onemg_order, data):
        """Handle order confirmation webhook"""
        onemg_order.onemg_status = 'confirmed'
        onemg_order.last_api_response = data
        onemg_order.save()

        onemg_order.pharmacy_order.status = 'confirmed'
        onemg_order.pharmacy_order.save()

        notify_user(
            onemg_order.pharmacy_order.user,
            "Order Confirmed",
            f"Your pharmacy order {onemg_order.pharmacy_order.order_id} has been confirmed by 1MG.",
            item_type="pharmacy_order"
        )

    def _handle_order_packed(self, onemg_order, data):
        """Handle order packed webhook"""
        onemg_order.onemg_status = 'packed'
        onemg_order.last_api_response = data
        onemg_order.save()

        onemg_order.pharmacy_order.status = 'processing'
        onemg_order.pharmacy_order.save()

    def _handle_order_shipped(self, onemg_order, data):
        """Handle order shipped webhook"""
        onemg_order.onemg_status = 'shipped'
        onemg_order.tracking_number = data.get('tracking_number', '')
        onemg_order.tracking_url = data.get('tracking_url', '')
        onemg_order.courier_name = data.get('courier_name', '')
        onemg_order.shipped_at = timezone.now()
        onemg_order.last_api_response = data
        onemg_order.save()

        onemg_order.pharmacy_order.status = 'shipped'
        onemg_order.pharmacy_order.save()

        notify_user(
            onemg_order.pharmacy_order.user,
            "Order Shipped",
            f"Your pharmacy order {onemg_order.pharmacy_order.order_id} has been shipped. "
            f"Tracking: {onemg_order.tracking_number}",
            item_type="pharmacy_order"
        )

    def _handle_out_for_delivery(self, onemg_order, data):
        """Handle out for delivery webhook"""
        onemg_order.onemg_status = 'out_for_delivery'
        onemg_order.last_api_response = data
        onemg_order.save()

        onemg_order.pharmacy_order.status = 'out_for_delivery'
        onemg_order.pharmacy_order.save()

        notify_user(
            onemg_order.pharmacy_order.user,
            "Out for Delivery",
            f"Your pharmacy order {onemg_order.pharmacy_order.order_id} is out for delivery!",
            item_type="pharmacy_order"
        )

    def _handle_order_delivered(self, onemg_order, data):
        """Handle order delivered webhook"""
        onemg_order.onemg_status = 'delivered'
        onemg_order.actual_delivery_date = timezone.now()
        onemg_order.last_api_response = data
        onemg_order.save()

        onemg_order.pharmacy_order.status = 'delivered'
        onemg_order.pharmacy_order.save()

        notify_user(
            onemg_order.pharmacy_order.user,
            "Order Delivered",
            f"Your pharmacy order {onemg_order.pharmacy_order.order_id} has been delivered!",
            item_type="pharmacy_order"
        )

    def _handle_order_cancelled(self, onemg_order, data):
        """Handle order cancelled webhook"""
        onemg_order.onemg_status = 'cancelled'
        onemg_order.last_api_response = data
        onemg_order.save()

        onemg_order.pharmacy_order.status = 'cancelled'
        onemg_order.pharmacy_order.save()

        reason = data.get('reason', 'No reason provided')
        notify_user(
            onemg_order.pharmacy_order.user,
            "Order Cancelled",
            f"Your pharmacy order {onemg_order.pharmacy_order.order_id} has been cancelled. Reason: {reason}",
            item_type="pharmacy_order"
        )

    def _handle_order_stuck(self, onemg_order, data):
        """Handle order stuck webhook"""
        # Log but don't change status, requires manual intervention
        onemg_order.last_api_response = data
        onemg_order.save()

        logger.warning(f"Order stuck: {onemg_order.onemg_order_id}")

    def _handle_prescription_rejected(self, onemg_order, data):
        """Handle prescription rejected webhook"""
        onemg_order.prescription_verified = False
        onemg_order.prescription_rejection_reason = data.get('reason', '')
        onemg_order.last_api_response = data
        onemg_order.save()

        notify_user(
            onemg_order.pharmacy_order.user,
            "Prescription Issue",
            f"There was an issue with the prescription for order {onemg_order.pharmacy_order.order_id}. "
            f"Reason: {data.get('reason', 'Please upload a valid prescription.')}",
            item_type="pharmacy_order"
        )


# ============================================
# Health Check API
# ============================================

class OneMGHealthCheckAPIView(APIView):
    """
    Check health of 1MG integration
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = get_onemg_service()
        health = service.health_check()
        return Response(health)
