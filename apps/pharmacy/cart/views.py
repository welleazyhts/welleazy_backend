from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.pharmacy.models import Medicine
from .models import Cart, CartItem , Coupon , Prescription
from .serializers import CartSerializer , PrescriptionSerializer , CartItemSerializer
from django.shortcuts import get_object_or_404
from apps.addresses.models import Address , AddressType
from apps.addresses.serializers import AddressSerializer,AddressTypeSerializer
from apps.pharmacy.cart.utils import estimate_delivery_date
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
import mimetypes
from apps.pharmacy.models import PharmacyOrder , PharmacyOrderItem
from datetime import datetime
from apps.notifications.utils import notify_user

# Create your views here.


# Adding And Removing From The Cart

class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        medicine_id = request.data.get("medicine_id")
        quantity = int(request.data.get("quantity", 1))

        if not medicine_id:
            return Response({"error": "medicine_id is required"}, status=400)

        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)

        cart, _ = Cart.objects.get_or_create(user=user)

        # Vendor auto-assigned from medicine
        vendor = medicine.vendor

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            medicine=medicine,
            
        )
        if created:
            item.quantity = quantity
            item.created_by=request.user
            
        else:
            item.quantity += quantity
        item.updated_by=request.user
        item.save()

        item_data= CartItemSerializer(item).data

        return Response({"message": "Added to cart successfully", "item":item_data}, status=201)
    
# class UpdateCartItemAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, item_id):
#         try:
#             item = CartItem.objects.get(id=item_id)
#         except CartItem.DoesNotExist:
#             return Response({"error": "Item not found"}, status=404)

#         qty = request.data.get("quantity")
#         if qty:
#             item.quantity = qty
#             item.created_by=request.user
#             item.save()

#         item_data = CartItemSerializer(item).data

#         return Response({"message": "Updated","data": item_data}, status=200)
    
class RemoveCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id)
            item.delete()
            return Response({"message": "Item removed"}, status=200)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)


class IncreaseQuantityAPIView(APIView):

    def post(self, request):
        item_id = request.data.get("item_id")

        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity += 1
        cart_item.save()

        return Response({"message": "Quantity increased"}, status=200)
    

class DecreaseQuantityAPIView(APIView):

    def post(self, request):
        item_id = request.data.get("item_id")

        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity -= 1

        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()

        return Response({"message": "Quantity updated"}, status=200)


class GetCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # If cart has NO items
        if cart.items.count() == 0:
            return Response(
                {"message": "Your cart is empty", "cart": None},
                status=200
            )

        # Auto-set default address if not selected
        if cart.address is None:
            default_address = Address.objects.filter(
                user=request.user,
                is_default=True
            ).first()

            if default_address:
                cart.address = default_address
                cart.save()

        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data, status=200)

    

# Coupon Apply And Remove From The Cart API


class ApplyCouponAPIView(APIView):

    def post(self, request):
        user = request.user
        coupon_code = request.data.get("coupon")

        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
        except Coupon.DoesNotExist:
            return Response({"error": "Invalid coupon code"}, status=400)

        cart, _ = Cart.objects.get_or_create(user=user)

        # check cart value eligibility
        if cart.total_selling < coupon.min_cart_value:
            return Response({"error": "Cart amount too low for this coupon"}, status=400)

        cart.coupon = coupon
        cart.save()

        return Response({"message": "Coupon applied"}, status=200)
    

class RemoveCouponAPIView(APIView):
    def post(self, request):
        user = request.user

        cart, _ = Cart.objects.get_or_create(user=user)
        cart.coupon = None
        cart.save()

        return Response({"message": "Coupon removed"}, status=200)
    

# Address selection or Adding to the Cart API


class AddressTypeListAPIView(APIView):
    def get(self, request):
        types = AddressType.objects.filter()
        serializer = AddressTypeSerializer(types, many=True)
        return Response(serializer.data)
    
class AddressListAPIView(APIView):
    def get(self, request):
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)


class SetAddressTypeAPIView(APIView):

    def post(self, request):
        # address_id = request.data.get("address_id")
        address_type_id = request.data.get("address_type_id")

        user = request.user

        # Get address
        # address = get_object_or_404(Address, id=address_id, user=user)

        # Get address type
        address_type = get_object_or_404(AddressType, id=address_type_id)

        # Assign address type to address
        # address.address_type = address_type
        address_type.save()

        return Response(
            {"message": "Address type selected successfully"},
            status=200
        )


class SelectAddressForCartAPIView(APIView):

    def post(self, request):
        address_id = request.data.get("address_id")
        user = request.user

        address = get_object_or_404(Address, id=address_id, user=user)

        # ❗ Validate that address has a type
        if not address.address_type:
            return Response(
                {"error": "Please select address type before using this address"},
                status=400
            )

        cart, _ = Cart.objects.get_or_create(user=user)
        cart.address = address
        cart.save()

        return Response({"message": "Shipping address selected for cart"}, status=200)

class AddNewAddressAPIView(APIView):
    """
    Creates address for authenticated user (self).
    Accepts address_type_id refers to AddressType.id
    """

    def post(self, request):
        user = request.user

        # 1. Validate address_type_id
        address_type_id = request.data.get("address_type_id")
        if not address_type_id:
            return Response(
                {"address_type_id": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            address_type_obj = AddressType.objects.get(id=address_type_id)
        except AddressType.DoesNotExist:
            return Response(
                {"address_type_id": ["Invalid address_type_id"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        address_line1 = request.data.get("address_line1")
        city = request.data.get("city")
        state= request.data.get("state")
        pincode = request.data.get("pincode")
        landmark = request.data.get("landmark")
        address_line2 = request.data.get("address_line2")

        # 2. Validate required fields
        required_fields = ["address_line1", "city", "state", "pincode"]
        missing = [field for field in required_fields if not request.data.get(field)]

        if missing:
            return Response(
                {"error": [f"{field} is required." for field in missing]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        for idx, field in enumerate(required_fields):
            if not field:
                return Response(
                    {"error":[f"{missing[idx]} is required."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
        existing = Address.objects.filter(
            user=user,
            address_line1__iexact=address_line1,
            state__iexact=state,
            city__iexact=city,
           
        ).first()

        if existing:
            return Response(
                {"message": "Address with same details already exists.",
                 },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Create address (SELF ONLY)
        address = Address.objects.create(
            user=user,
            dependant=None,
            relationship=None,
            address_type=address_type_obj,
            address_line1=request.data.get("address_line1"),
            address_line2=request.data.get("address_line2"),
            landmark=request.data.get("landmark"),
            city=request.data.get("city"),
            state=request.data.get("state"),
            pincode=request.data.get("pincode"),
            created_by=request.user,
        )

        return Response(
            {
                "message": "Address created successfully",
                "address_id": address.id,
                "address": AddressSerializer(address).data,
            },
            status=status.HTTP_201_CREATED,
        )




class UpdateAddressAPIView(APIView):

    def put(self, request, pk):
        address = get_object_or_404(Address, id=pk, user=request.user)

        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Address updated", "data": serializer.data}, status=200)

        return Response(serializer.errors, status=400)



# DELIVERY ESTIMATION API
class EstimateDeliveryAPIView(APIView):
    def post(self, request):
        pincode = request.data.get("pincode")
        if not pincode:
            return Response({"error": "Pincode is required"}, status=400)

        date = estimate_delivery_date(pincode)
        return Response({
            "deliver_by": date.strftime("%A, %d %B %Y")
        })

#PRESCRIPTION UPLOAD API

class UploadPrescriptionAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        notes = request.data.get("notes", "")

        if not file:
            return Response({"error": "File is required"}, status=400)

        pres = Prescription.objects.create(
            user=request.user,
            file=file,
            notes=notes,
            type="uploaded"
        )
        
        cart, _ =Cart.objects.get_or_create(user=request.user)

        cart.prescription = pres
        
        cart.save()



        return Response({
            "message": "Prescription uploaded and added to cart successfully",
            "data": PrescriptionSerializer(pres).data
        }, status=201)
    

# class AddEPrescriptionAPIView(APIView):
#     def post(self, request):
#         doctor_name = request.data.get("doctor_name")
#         diagnosis = request.data.get("diagnosis")
#         prescribed_date = request.data.get("prescribed_date")
#         file = request.data.get("file", None)  # optional PDF

#         if not doctor_name or not diagnosis:
#             return Response({"error": "doctor_name and diagnosis are required"}, status=400)

#         pres = Prescription.objects.create(
#             user=request.user,
#             doctor_name=doctor_name,
#             diagnosis=diagnosis,
#             prescribed_date=prescribed_date,
#             file=file,
#             type="e_prescription"
#         )

#         return Response({
#             "message": "E-prescription created successfully",
#             "data": PrescriptionSerializer(pres).data
#         }, status=201)



class ListPrescriptionsAPIView(APIView):

    def get(self, request):
        pres = Prescription.objects.filter(user=request.user).order_by("-created_at")
        serializer = PrescriptionSerializer(pres, many=True)
        return Response(serializer.data)
    
# class ListEprescriptionsAPIView(APIView):
#     def get(self, request):
#         pres = Prescription.objects.filter(user=request.user, type="e_prescription")
#         return Response(PrescriptionSerializer(pres, many=True).data)

    
class DownloadPrescriptionAPIView(APIView):

    def get(self, request, pk):
        prescription = get_object_or_404(
            Prescription, 
            id=pk,
            user=request.user     # Security: only owner can download
        )

        file_path = prescription.file.path
        file_name = prescription.file.name.split("/")[-1]

        content_type, _ = mimetypes.guess_type(file_path)

        response = FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=file_name,
            content_type=content_type or "application/octet-stream"
        )
        return response
    

# DELIVERY MODE HOME OR COD API

class SetDeliveryModeAPIView(APIView):

    def post(self, request):
        mode = request.data.get("delivery_mode")

        if mode not in ["home_delivery", "cod"]:
            return Response({"error": "Invalid delivery mode"}, status=400)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.delivery_mode = mode
        cart.created_by=self.request.user
        cart.save()

        return Response({
            "message": "Delivery mode updated successfully",
            "delivery_mode": mode
        })



class PharmacyOrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # 1️⃣ Get Cart
        cart = Cart.objects.get_or_create(user=user) [0]


        if cart.items.count() == 0:
            return Response({"error": "Cart is empty"}, status=400)

        if not cart.address:
            return Response({"error": "Please select a delivery address"}, status=400)

        if not cart.delivery_mode:
            return Response({"error": "Please choose a delivery mode"}, status=400)

        # 2️⃣ Calculate totals
        subtotal = cart.total_selling
        coupon_discount = 0

        if cart.coupon:
            coupon=cart.coupon

            if subtotal >= cart.coupon.min_cart_value:

                if hasattr(coupon, "discount_percent") and coupon.discount_percent:
                    coupon_discount = round((subtotal *coupon.discount_percent / 100), 2)
                
                elif hasattr(coupon, "discount_amount") and coupon.discount_amount:
                    coupon_discount= float(coupon.discount_amount)
                elif hasattr(coupon, "discount_amount") and coupon.discount_amount:
                    coupon_discount = float(coupon.discount_amount)

                # 2C. Max discount (optional)
                if hasattr(coupon, "max_discount_amount") and coupon.max_discount_amount:
                    coupon_discount = min(
                        coupon_discount,
                        float(coupon.max_discount_amount)
                    )

        total_amount = max(subtotal - coupon_discount, 0)

     
        # 3️⃣ Delivery Date
        expected_date = estimate_delivery_date(cart.address.pincode)

        # 4️⃣ Generate a unique Order ID
        order_id = f"PHAR-{int(datetime.now().timestamp())}"

        # 5️⃣ CREATE PharmacyOrder
        order = PharmacyOrder.objects.create(
            order_id=order_id,
            user=user,
            patient_name=user.name if hasattr(user, "name") else user.email ,
            order_type=cart.delivery_mode,
            status="confirmed",
            ordered_date=datetime.today().date(),
            expected_delivery_date=expected_date,
            total_amount=total_amount,
            address=cart.address
        )

        # 6️⃣ Add prescription file to order (if exists)
        if cart.prescription:
            order.prescription_file = cart.prescription.file
            order.save()

        # 7️⃣ Move cart items → PharmacyOrderItems
        for item in cart.items.all():
            PharmacyOrderItem.objects.create(
                order=order,
                medicine=item.medicine,
                quantity=item.quantity,
                amount=item.quantity * item.medicine.selling_price
            )

        # 8️⃣ Clear Cart after creating order
        cart.items.all().delete()
        cart.coupon = None
        cart.prescription = None
        cart.save()

        when = expected_date  # date object
        formatted_date = when.strftime('%d %b %Y')

        notify_user(
            request.user,
            "Pharmacy Order Placed",
            f"Your pharmacy order {order.order_id} has been placed successfully.\n"
            f"Expected delivery date: {formatted_date}.",
            item_type="pharmacy_order"
        )
        # 9️⃣ Return success
        return Response({
            "message": "Order placed successfully!",
            "order_id": order.order_id,
            "summary": {
                "items": order.items.count(),
                "subtotal": float(subtotal),
                "coupon_discount": float(coupon_discount),
                "total_payable": float(total_amount),
                "delivery_mode": order.order_type,
                "expected_delivery_date": expected_date,
            }
        }, status=201)


class PharmacyOrderListAPIView(APIView):
    """
    Get list of user's pharmacy orders
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = PharmacyOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')

        orders_data = []
        for order in orders:
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'id': item.id,
                    'medicine': {
                        'id': item.medicine.id,
                        'name': item.medicine.name,
                        'selling_price': float(item.medicine.selling_price),
                        'image': item.medicine.image.url if item.medicine.image else None,
                    },
                    'quantity': item.quantity,
                    'amount': float(item.amount),
                })

            orders_data.append({
                'order_id': order.order_id,
                'patient_name': order.patient_name,
                'order_type': order.order_type,
                'status': order.status,
                'ordered_date': order.ordered_date.isoformat() if order.ordered_date else None,
                'expected_delivery_date': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                'total_amount': float(order.total_amount),
                'items': items_data,
                'created_at': order.created_at.isoformat(),
            })

        return Response(orders_data)


class PharmacyOrderDetailAPIView(APIView):
    """
    Get details of a specific pharmacy order
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = PharmacyOrder.objects.get(
                order_id=order_id,
                user=request.user
            )
        except PharmacyOrder.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        items_data = []
        for item in order.items.all():
            items_data.append({
                'id': item.id,
                'medicine': {
                    'id': item.medicine.id,
                    'name': item.medicine.name,
                    'selling_price': float(item.medicine.selling_price),
                    'mrp': float(item.medicine.mrp_price),
                    'image': item.medicine.image.url if item.medicine.image else None,
                },
                'quantity': item.quantity,
                'amount': float(item.amount),
            })

        address_data = None
        if order.address:
            address_data = {
                'address_line1': order.address.address_line1,
                'address_line2': order.address.address_line2,
                'city': order.address.city,
                'state': order.address.state,
                'pincode': order.address.pincode,
            }

        return Response({
            'order_id': order.order_id,
            'patient_name': order.patient_name,
            'order_type': order.order_type,
            'status': order.status,
            'ordered_date': order.ordered_date.isoformat() if order.ordered_date else None,
            'expected_delivery_date': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
            'total_amount': float(order.total_amount),
            'items': items_data,
            'address': address_data,
            'created_at': order.created_at.isoformat(),
        })
