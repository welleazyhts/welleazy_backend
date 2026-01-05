# apps/payments/views.py

import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.appointments.models import Cart
from apps.appointments.models import Appointment as AppointmentModel, AppointmentItem

from django.views.generic import TemplateView

class CreateRazorpayOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cart_id):

        cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        items = cart.items.all()

        if not items.exists():
            return Response({"detail": "Cart is empty"}, status=400)

        # Final payable amount after discounts
        final_amount = sum(float(item.final_price or 0) for item in items)
        amount_paise = int(final_amount * 100)   # Razorpay expects paise

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # Create Order
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "cart_id": str(cart.id),
                "user_id": str(request.user.id)
            }
        })

        return Response({
            "message": "Order created successfully",
            "order_id": order["id"],
            "amount": final_amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID
        })

class RazorpayVerifyPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get("razorpay_payment_id")
        order_id = request.data.get("razorpay_order_id")
        signature = request.data.get("razorpay_signature")

        if not all([payment_id, order_id, signature]):
            return Response({"detail": "Missing fields"}, status=400)

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # Verify Razorpay signature
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
        except:
            return Response({"detail": "Invalid payment signature"}, status=400)

        # Fetch the order to get cart_id
        order_info = client.order.fetch(order_id)
        cart_id = order_info["notes"].get("cart_id")

        # Fetch payment details for mode/bank info
        payment_info = client.payment.fetch(payment_id)
        payment_mode = payment_info.get("method", "Unknown")
        payment_bank = payment_info.get("bank")
        payment_last4 = payment_info.get("last4")

        cart = get_object_or_404(Cart, id=cart_id)
        items = cart.items.all()

        if not items.exists():
            return Response({"detail": "Cart is empty"}, status=400)

        created = []

        # Create appointments
        for item in items:
            appt = AppointmentModel.objects.create(
                user=request.user,
                diagnostic_center=item.diagnostic_center,
                visit_type=item.visit_type,
                for_whom=item.for_whom,
                dependant=item.dependant,
                address=item.address,
                note=item.note,
                status="confirmed",
                # Save Payment Info
                payment_transaction_id=payment_id,
                payment_mode=payment_mode,
                payment_bank=payment_bank,
                payment_last4=payment_last4,
                payment_reference=order_id,
                created_by=request.user,
                updated_by=request.user
            )

            for t in item.tests.all():
                AppointmentItem.objects.create(
                    appointment=appt,
                    test=t,
                    price=t.price
                )

            created.append({
                "appointment_id": appt.id,
                "diagnostic_center": appt.diagnostic_center.name,
                "tests": [t.name for t in item.tests.all()],
                "transaction_id": payment_id
            })

        # Empty cart after payment
        cart.items.all().delete()

        return Response({
            "message": "Payment verified, appointments confirmed",
            "appointments": created
        })


class RazorpayPaymentPageView(TemplateView):
    template_name = "payments/payment_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart_id"] = kwargs.get("cart_id")
        
        context["access_token"] = self.request.GET.get("token", "")
        return context


from django.db.models import Sum
from .serializers import MyTransactionSerializer
from apps.pharmacy.models import PharmacyOrder

class MyTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Fetch Appointments
        appointments = AppointmentModel.objects.filter(user=user).select_related(
            'invoice_detail', 
            'doctor__doctor', 
            'diagnostic_center'
        ).order_by('-created_at')
        
        # Fetch Pharmacy Orders
        pharmacy_orders = PharmacyOrder.objects.filter(user=user).order_by('-created_at')
        
        # Aggregated list for transactions
        transactions_list = []
        
        total_spent = 0.0
        total_pending = 0.0
        
        # Buckets (aligning with my_bookings)
        COMPLETED_STATUS = ['completed', 'delivered', 'done', 'confirmed', 'paid']
        PENDING_STATUS = ['pending', 'scheduled', 'booked', 'upcoming']

        # Process Appointments
        for appt in appointments:
            appt_data = MyTransactionSerializer(appt).data
            amount = float(appt_data.get('amount') or 0)
            
            if appt.status.lower() in COMPLETED_STATUS:
                total_spent += amount
            elif appt.status.lower() in PENDING_STATUS:
                total_pending += amount
                
            transactions_list.append(appt_data)
            
        # Process Pharmacy Orders
        for order in pharmacy_orders:
            amount = float(order.total_amount or 0)
            
            if order.status.lower() in COMPLETED_STATUS:
                total_spent += amount
            elif order.status.lower() in PENDING_STATUS:
                total_pending += amount
                
            transactions_list.append({
                'id': order.id,
                'transaction_id': order.order_id,
                'title': f"Pharmacy Order {order.order_id}",
                'amount': amount,
                'date': order.ordered_date,
                'status': order.status,
                'payment_method': order.order_type
            })

        transactions_list.sort(key=lambda x: str(x['date']), reverse=True)

        return Response({
            "summary": {
                "total_spent": round(total_spent, 2),
                "refund": 0.0, # Not implemented yet
                "pending": round(total_pending, 2)
            },
            "transactions": transactions_list
        })
