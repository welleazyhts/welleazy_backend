from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status 
from rest_framework.response import Response
from .models import Cart, CartItem, Appointment , AppointmentItem
from .serializers import AddToCartSerializer, CartItemSerializer, AddPackageToCartSerializer , DoctorAvailabilitySerializer
from django.shortcuts import get_object_or_404
from apps.labtest.models import Test
from apps.diagnostic_center.models import DiagnosticCenter
from apps.labfilter.models import VisitType
from apps.addresses.models import Address
from apps.dependants.models import Dependant
from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage
from apps.doctor_details.models import DoctorProfessionalDetails

from datetime import datetime, date, time
from .models import DiagnosticCenter , DoctorAvailability , AppointmentVoucher
from .utils import generate_time_slots_for_center, get_slot_booked_count
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Count
from .models import DiagnosticCenter ,  ReportDocument
from django.db import transaction
from .serializers import DoctorAppointmentToCartSerializer , AppointmentVoucherSerializer
from rest_framework.decorators import action
from apps.consultation_filter.models import DoctorSpeciality

from apps.notifications.utils import notify_user
from decimal import Decimal
from rest_framework import viewsets, status



class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = AddToCartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # get or create user's active cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        dc = DiagnosticCenter.objects.get(id=data['diagnostic_center_id'])
        vt = VisitType.objects.get(id=data['visit_type_id'])
        tests = Test.objects.filter(id__in=data['test_ids'])
        dependant = None
        if not data['for_whom'] == "self":
            dependant = Dependant.objects.get(id=data['dependant_id'])
        address = None
        if 'address_id' in data and data['address_id']:
            address = Address.objects.get(id=data['address_id'])

        # optional estimate price as sum of test prices (center price override logic could be added)
        estimated_price = None
        try:
            estimated_price = sum((t.price or 0) for t in tests)
        except Exception:
            estimated_price = None

        cart_item = CartItem(
            cart=cart,
            diagnostic_center=dc,
            visit_type=vt,
            for_whom=data['for_whom'],
            dependant=dependant,
            address=address,
            note=data.get('note'),
            price=estimated_price,
            created_by=request.user,
            updated_by=request.user
        )
        cart_item.save() 
        cart_item.tests.set(tests)
        cart_item.apply_discount() 
        out = CartItemSerializer(cart_item).data
        return Response(
            {
                "message": "Test added to cart",
                "data": out
            },
            status=status.HTTP_201_CREATED
        )

class UserCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        serializer = CartItemSerializer(items, many=True, context={"mode": "cart"})

        return Response({
            "message": "User cart retrieved successfully",
            "cart_id": cart.id, 
            "items": serializer.data,
            "total_items": items.count()
        }, status=status.HTTP_200_OK)


class CheckoutCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cart_id):
        cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        items = cart.items.all()

        if not items.exists():
            return Response({"detail": "Cart is empty."}, status=400)

        total_amount = 0
        total_discount = 0
        final_payable = 0

        checkout_items = []
        for item in items:
            item.apply_discount()

            base_price = float(item.price or item.consultation_fee or 0)
            discount =float(item.discount_amount or 0)
            final_price=float(item.final_price or base_price)


            total_amount += base_price
            total_discount += discount
            final_payable += final_price


        # DOCTOR DETAILS-------

            doctor_info = None
            if item.item_type == "doctor_appointment":
                doctor_info = {
                    "doctor_id": item.doctor.id if item.doctor else None,
                    "doctor_name": item.doctor.doctor.full_name if item.doctor else None,
                    "specialization": item.specialization.name if item.specialization else None,
                    "appointment_date": item.appointment_date,
                    "appointment_time": item.appointment_time,
                    "mode": item.mode,
                    "consultation_fee": float(item.consultation_fee or 0),
                    "for_whom": item.for_whom,
                    "dependant": item.dependant.id if item.dependant else None,
                    "patient_name": item.patient_name,
                    "symptoms": item.symptoms,
                    "note": item.note,
                }


            # EYE -DENTAL DETASILS-----

            # eye_dental_info = None
            # if item.item_type in ["eye_appointment", "dental_appointment"]:
            #     eye_dental_info = {
            #         "vendor": item.vendor.id if item.vendor else None,
            #         "eye_center": item.eye_vendor_centers.id if item.eye_vendor_centers else None,
            #         "dental_center": item.dental_vendor_centers.id if item.dental_vendor_centers else None,
            #         "appointment_date": item.appointment_date,
            #         "appointment_time": item.appointment_time,
            #         "consultation_fee": float(item.consultation_fee or 0),
            #         "for_whom": item.for_whom,
            #         "patient_name": item.patient_name,
            #         "dependant": item.dependant.id if item.dependant else None,
            #         "note": item.note,
            #     } 

            # LAB DETAILS------
            lab_info = None
            if item.item_type == "appointment":  # lab test appointment
                lab_info = {
                    "diagnostic_center": item.diagnostic_center.name if item.diagnostic_center else None,
                    "tests": [t.name for t in item.tests.all()],
                    "visit_type": item.visit_type.name if item.visit_type else None,
                    "address": str(item.address) if item.address else None,
                    "selected_date": item.selected_date,
                    "selected_time": item.selected_time,
                }


            # ------------------------------------------------------------------------------
            # HEALTH PACKAGE DETAILS
            # ------------------------------------------------------------------------------
            health_package_info = None
            if item.item_type == "health_package" and item.health_package:
                health_package_info = {
                    "package_id": item.health_package.id,
                    "name": item.health_package.name,
                    "price": float(item.health_package.price or 0),
                    "validity_till": item.health_package.validity_till,
                    "tests": [t.name for t in item.health_package.tests.all()],
                }

            # ------------------------------------------------------------------------------
            # SPONSORED PACKAGE DETAILS
            # ------------------------------------------------------------------------------
            sponsored_package_info = None
            if item.item_type == "sponsored_package" and item.sponsored_package:
                sponsored_package_info = {
                    "package_id": item.sponsored_package.id,
                    "name": item.sponsored_package.name,
                    "price": float(item.sponsored_package.price or 0),
                    "description": item.sponsored_package.description,
                    "validity_till": item.sponsored_package.validity_till,
                    "tests": [t.name for t in item.sponsored_package.tests.all()],
                }

            checkout_items.append({
                    "cart_item_id": item.id,
                    "item_type": item.item_type,
                    "price": base_price,
                    "discount": discount,
                    "final_price": final_price,
                    "doctor_appointment": doctor_info,
                    
                    "lab_appointment": lab_info,
                    "health_package": health_package_info,
                    "sponsored_package": sponsored_package_info,
                })
        

        return Response({
            "message": "Checkout details retrieved successfully",
            "cart_id": cart.id,
            "total_amount": total_amount,
            "total_discount": total_discount,
            "final_payable": final_payable,
            "items": CartItemSerializer(items, many=True).data
        })
    

 

class ConfirmCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
          # ONLY FOR TESTING NOW PURPOSE---
          
    def post(self, request, cart_id):
        cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        items = cart.items.all()

        if not items.exists():
            return Response({"detail": "Cart is empty"}, status=400)

        created = []

        for item in items:

            scheduled_at = None

            if item.appointment_date and item.appointment_time:
                scheduled_at = datetime.combine(item.appointment_date, item.appointment_time)

            elif item.selected_date and item.selected_time:
                scheduled_at = datetime.combine(item.selected_date, item.selected_time)

            # ----------------------------------------------------------------------------
            # DOCTOR APPOINTMENT CREATION
            # ----------------------------------------------------------------------------
            if item.item_type == "doctor_appointment":
                appt = Appointment.objects.create(
                    user=request.user,
                    item_type="doctor_appointment",
                    doctor=item.doctor,
                    for_whom=item.for_whom,
                    dependant=item.dependant,
                    note=item.note,
                    patient_name = item.patient_name,
                    mode=item.mode,
                    scheduled_at=scheduled_at,
                    status="pending"
                )

                created.append({
                    "appointment_id": appt.id,
                    "type": "doctor_appointment",
                    "doctor": item.doctor.doctor.full_name,
                    "date": item.appointment_date,
                    "time": item.appointment_time,
                })


            # elif item.item_type in ["eye_appointment", "dental_appointment"]:
            #     appt = Appointment.objects.create(
            #         user=request.user,
            #         item_type=item.item_type,
            #         vendor=item.vendor,
            #         eye_vendor_centers=item.eye_vendor_centers,
            #         for_whom=item.for_whom,
            #         dependant=item.dependant,
            #         note=item.note,
            #         patient_name= item.patient_name,
            #         scheduled_at=scheduled_at,
            #         status="confirmed",
            #     )
            #     when=timezone.localtime(scheduled_at) if timezone.is_aware(scheduled_at) else scheduled_at
            #     notify_user(
            #         request.user,
            #         "Eye Appointment Confirmed",
            #         f"Your eye appointment is confirmed for "
            #         f"{when.strftime('%d %b %Y')} at {when.strftime('%I:%M %p')}.",
            #         item_type="eye_appointment"
            #     )

            #     created.append({
            #         "appointment_id": appt.id,
            #         "type": "eye_appointment",
            #         "date": item.appointment_date or item.selected_date,
            #         "time": item.appointment_time or item.selected_time,
            #     })

            # ---------------------------------------------------------
            # DENTAL APPOINTMENT
            # ---------------------------------------------------------
            # elif item.item_type == "dental_appointment":
            #     appt = Appointment.objects.create(
            #         user=request.user,
            #         item_type="dental_appointment",
            #         vendor=item.vendor,
            #         dental_vendor_centers=item.dental_vendor_centers,
            #         for_whom=item.for_whom,
            #         dependant=item.dependant,
            #         note=item.note,
            #         patient_name= item.patient_name,
            #         scheduled_at=scheduled_at,
            #         status="pending"
            #     )

            #     created.append({
            #         "appointment_id": appt.id,
            #         "type": item.item_type,
            #         "date": item.appointment_date,
            #         "time": item.appointment_time,
            #     })


            # ----------------------------------------------------------------------------
            # LAB APPOINTMENT CREATION
            # ----------------------------------------------------------------------------
            elif item.item_type == "test":  
                appt = Appointment.objects.create(
                    user=request.user,
                    item_type="lab_appointment",
                    diagnostic_center=item.diagnostic_center,
                    visit_type=item.visit_type,
                    for_whom=item.for_whom,
                    dependant=item.dependant,
                    address=item.address,
                    note=item.note,
                    scheduled_at=scheduled_at,
                    status="pending",
                )

                for t in item.tests.all():
                    AppointmentItem.objects.create(
                        appointment=appt,
                        test=t,
                        price=t.price
                    )

                created.append({
                    "appointment_id": appt.id,
                    "type": "lab_appointment",
                    "tests": [t.name for t in item.tests.all()],
                    "date": item.selected_date,
                    "time": item.selected_time,
                })


            # ==========================================================
            # 4️⃣ HEALTH PACKAGE APPOINTMENT
            # ==========================================================
            elif item.item_type == "health_package" and item.health_package:
                appt = Appointment.objects.create(
                    user=request.user,
                    item_type="health_package",
                    diagnostic_center=item.diagnostic_center,
                    for_whom=item.for_whom,
                    dependant=item.dependant,
                    scheduled_at=scheduled_at, 
                    note=item.note,
                    status="pending"
                )

                # Add package tests inside AppointmentItem
                for t in item.health_package.tests.all():
                    AppointmentItem.objects.create(
                        appointment=appt,
                        test=t,
                        price=t.price
                    )

                created.append({
                    "appointment_id": appt.id,
                    "type": "health_package",
                    "package": item.health_package.name,
                    "tests": [t.name for t in item.health_package.tests.all()],
                    "date": item.selected_date,
                    "time": item.selected_time,

                })

            # ==========================================================
            # 5️⃣ SPONSORED PACKAGE APPOINTMENT
            # ==========================================================
            elif item.item_type == "sponsored_package" and item.sponsored_package:
                appt = Appointment.objects.create(
                    user=request.user,
                    item_type="sponsored_package",
                    diagnostic_center=item.diagnostic_center,
                    for_whom=item.for_whom,
                    dependant=item.dependant,
                    scheduled_at=scheduled_at,   
                    note=item.note,
                    status="pending"
                )

                # Add sponsored package tests
                for t in item.sponsored_package.tests.all():
                    AppointmentItem.objects.create(
                        appointment=appt,
                        test=t,
                        price=t.price
                    )

                created.append({
                    "appointment_id": appt.id,
                    "type": "sponsored_package",
                    "package": item.sponsored_package.name,
                    "tests": [t.name for t in item.sponsored_package.tests.all()],
                    "date": item.selected_date,
                    "time": item.selected_time,
                })
        # Finally clear cart
        cart.items.all().delete()

        return Response({
            "message": "Checkout completed",
            "appointments": created
        }, status=201)



class AddPackageToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = AddPackageToCartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        cart, _ = Cart.objects.get_or_create(user=request.user)
        dc = DiagnosticCenter.objects.get(id=data["diagnostic_center_id"])
        dependant = None
        if not data["for_whom"] == "self":
            dependant = Dependant.objects.get(id=data["dependant_id"])

        # resolve package
        health_package = sponsored_package = None
        price = 0
        if data["item_type"] == "health_package":
            health_package = HealthPackage.objects.get(id=data["package_id"])
            price = health_package.price or 0
        else:
            sponsored_package = SponsoredPackage.objects.get(id=data["package_id"])
            price = sponsored_package.price or 0


        from datetime import datetime

        appointment_date_str = data.get("appointment_date")
        appointment_time_str = data.get("appointment_time")

        if not appointment_date_str or not appointment_time_str:
            return Response(
                {"error": "Appointment date and time are required."},
                status=400
        )


        try:
            appointment_date = datetime.strptime(appointment_date_str, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(appointment_time_str, "%I:%M %p").time()
        except ValueError:
            return Response({"error": "Invalid date or time format"}, status=400)

        existing_item=CartItem.objects.filter(
            cart=cart,
            diagnostic_center=dc,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        ).first()

        confirm_update = data.get("confirm_update", False)

        if existing_item:
            if not confirm_update:
                return Response(
                    {
                        "message": "An appointment already exists for this diagnostic center at the selected time.",
                        "action_required": "confirm_update",
                        "existing_item": CartItemSerializer(existing_item).data
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            existing_item.item_type = data["item_type"]
            existing_item.health_package = health_package
            existing_item.sponsored_package = sponsored_package
            existing_item.price = price
            existing_item.for_whom = data["for_whom"]
            existing_item.dependant = dependant
            existing_item.note = data.get("note")
            existing_item.updated_by = request.user
            existing_item.save()
            existing_item.apply_discount()

            return Response(
                {
                    "message": "Cart updated successfully",
                    "data": CartItemSerializer(existing_item).data
                },
                status=status.HTTP_200_OK
            )


        item = CartItem(
            cart=cart,
            item_type=data["item_type"],
            diagnostic_center=dc,
            for_whom=data["for_whom"],
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            dependant=dependant,
            health_package=health_package,
            sponsored_package=sponsored_package,
            price=price,
            note=data.get("note", None),
            created_by=request.user,
            updated_by=request.user
        )   
        item.save()
        item.apply_discount() 
        out = CartItemSerializer(item).data
        return Response(
            {
                "message": "Package added to cart",
                "data": out
            },
            status=status.HTTP_201_CREATED
        )



# FOR DOCTOR APPOINTMENT

# AVAILABLE DATES AND SLOTS FOR PERTICULAR DOCTOR----

# TO INSERT THE AVAILABILITY DATES
class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.all()
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


    def _parse_date(self, s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

    def _parse_time(self, s):
        try:
            return datetime.strptime(s, "%I:%M %p").time()
        except Exception:
            raise ValueError("Invalid time format. ")

    def _generate_slots(self, start_t: time, end_t: time, slot_minutes: int):
        # Yield (start_time, end_time) times as time objects (non-overlapping).
        # end_t is exclusive (last slot must fit fully).
        if slot_minutes <= 0:
            raise ValueError("slot_duration must be > 0")
        start_dt = datetime.combine(date.today(), start_t)
        end_dt = datetime.combine(date.today(), end_t)
        if end_dt <= start_dt:
            raise ValueError("end_time must be after start_time")

        delta = timedelta(minutes=slot_minutes)
        slots = []
        cur = start_dt
        while cur + delta <= end_dt:
            s = (cur.time(), (cur + delta).time())
            slots.append(s)
            cur = cur + delta
        return slots

    def create(self, request, *args, **kwargs):
        doctor_id = request.data.get("doctor")
        mode = request.data.get("mode")
        dates_list = request.data.get("dates")            
        single_date = request.data.get("date")           
        time_slots = request.data.get("time_slots")      
        start_time = request.data.get("start_time")      
        end_time = request.data.get("end_time")          
        slot_duration = request.data.get("slot_duration")

        # Basic validations
        if not doctor_id:
            return Response({"error": "doctor is required"}, status=400)
        if not mode:
            return Response({"error": "mode is required (tele/video)"}, status=400)

        # Verify doctor exists and supports mode
        try:
            doctor = DoctorProfessionalDetails.objects.get(id=doctor_id)
        except DoctorProfessionalDetails.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=404)

        if mode == "tele" and not doctor.e_consultation:
            return Response({"error": "Doctor not available for tele consultation"}, status=400)
        if mode == "video" and not doctor.in_clinic:
            return Response({"error": "Doctor not available for video consultation"}, status=400)

        # Build dates array
        dates = []
        if dates_list:
            if not isinstance(dates_list, list):
                return Response({"error": "dates must be a list of YYYY-MM-DD strings"}, status=400)
            for d in dates_list:
                try:
                    dates.append(self._parse_date(d))
                except ValueError as e:
                    return Response({"error": str(e)}, status=400)
        elif single_date:
            try:
                dates.append(self._parse_date(single_date))
            except ValueError as e:
                return Response({"error": str(e)}, status=400)
        else:
            return Response({"error": "Either 'dates' (list) or 'date' (single) is required"}, status=400)

        # Build slots per date
        slots_per_date = {}  # date -> list of (start_time, end_time) tuples (time objects)
        # Option A: explicit time_slots list
        if time_slots:
            if not isinstance(time_slots, list):
                return Response({"error": "time_slots must be a list of {start_time, end_time}"}, status=400)
            for d in dates:
                parsed = []
                for slot in time_slots:
                    if "start_time" not in slot or "end_time" not in slot:
                        return Response({"error": "Each time slot must have start_time and end_time"}, status=400)
                    try:
                        s = self._parse_time(slot["start_time"])
                        e = self._parse_time(slot["end_time"])
                    except ValueError as exc:
                        return Response({"error": str(exc)}, status=400)
                    if datetime.combine(date.today(), e) <= datetime.combine(date.today(), s):
                        return Response({"error": "end_time must be after start_time in each slot"}, status=400)
                    parsed.append((s, e))
                slots_per_date[d] = parsed

        # Option B: single range + slot_duration to auto-split
        elif start_time and end_time and slot_duration:
            try:
                s_time = self._parse_time(start_time)
                e_time = self._parse_time(end_time)
                sd = int(slot_duration)
            except ValueError as exc:
                return Response({"error": str(exc)}, status=400)
            for d in dates:
                try:
                    parsed = self._generate_slots(s_time, e_time, sd)
                except ValueError as exc:
                    return Response({"error": str(exc)}, status=400)
                slots_per_date[d] = parsed
        else:
            return Response({"error": "Either time_slots (list) OR start_time + end_time + slot_duration must be provided"}, status=400)

        created = []
        errors = []
        # Use a transaction so partial failures can be handled as desired
        with transaction.atomic():
            for d in dates:
                weekday = d.strftime("%A")
                slots = slots_per_date.get(d, [])
                for s_time, e_time in slots:
                    data = {
                        "doctor": doctor_id,
                        "mode": mode,
                        "date": d.isoformat(),
                        "day_of_week": weekday,
                        "start_time": s_time.strftime("%I:%M %p"),
                        "end_time": e_time.strftime("%I:%M %p"),
                        # slot_duration left to default or can be added from request
                    }
                    # if user provided slot_duration at top level, set it
                    if slot_duration:
                        data["slot_duration"] = int(slot_duration)

                    serializer = self.get_serializer(data=data)
                    try:
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        created.append(serializer.data)
                    except Exception as exc:
                        # Collect error and continue (or you could abort)
                        errors.append({"date": d.isoformat(), "start_time": s_time.strftime("%H:%M"), "error": str(exc)})

        if errors:
            return Response({"created": created, "errors": errors}, status=207)  # 207 Multi-Status
        return Response({"created": created}, status=status.HTTP_201_CREATED)
    

    from rest_framework.decorators import action

    @action(detail=False, methods=["get"])
    def doctor_slots(self, request):
        doctor_id = request.query_params.get("doctor")

        if not doctor_id:
            return Response({"error": "doctor is required"}, status=400)

        qs = DoctorAvailability.objects.filter(doctor_id=doctor_id).order_by("date", "start_time")

        data = [
            {
                "date": obj.date,
                "day": obj.day_of_week,
                "start_time": obj.start_time,
                "end_time": obj.end_time
            }
            for obj in qs
        ]

        return Response(data)

# SELECT THE DOCTOR FIRST-----
class SelectDoctorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        doctor_id = request.data.get("doctor_id")

        if not doctor_id:
            return Response(
                {"error": "doctor_id is required"},
                status=400
            )

        # Check doctor exists
        doctor = get_object_or_404(DoctorProfessionalDetails, id=doctor_id)

        # Auto-select specialization from doctor
        specializations = doctor.specialization.all()

        if not specializations.exists():
            return Response(
                {"error": "This doctor has no specialization assigned"},
                status=400
            )
        
        selected_specialization = specializations.first()
        # Save in session
        request.session["selected_doctor_id"] = doctor.id
        request.session["selected_specialization_id"] = selected_specialization.id
        request.session.modified =True

        

        return Response({
            "message": "Doctor & specialization selected successfully",
            "doctor_id": doctor_id,
            "doctor_name":doctor.doctor.full_name,
            "specialities": [{"id":s.id , "name":s.name} for s in specializations]
        }, status=200)


 # DOCTOR APPOINTMENTS-----
class AppointmentToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        user = request.user

        # ---------------------------------------------------------
        # STEP 1: Doctor & Specialization must be pre-selected
        # ---------------------------------------------------------
        doctor_id = request.session.get("selected_doctor_id")
        specialization_id = request.session.get("selected_specialization_id")

        if not doctor_id or not specialization_id:
            return Response(
                {"error": "Doctor not selected"},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctor = get_object_or_404(DoctorProfessionalDetails, id=doctor_id)
        specialization = get_object_or_404(DoctorSpeciality, id=specialization_id)

        # ---------------------------------------------------------
        # STEP 2: for_whom (self / dependant)
        # ---------------------------------------------------------
        for_whom = data.get("for_whom")
        if for_whom not in ["self", "dependant"]:
            return Response({"error": "for_whom must be 'self' or 'dependant'."}, status=400)

        dependant = None
        if for_whom == "dependant":
            dependant_id = data.get("dependant_id") or data.get("dependant")
            if not dependant_id:
                return Response({"error": "dependant_id is required"}, status=400)

            dependant = get_object_or_404(Dependant, id=dependant_id, user=user)

        # ---------------------------------------------------------
        # STEP 3: Validate date & time
        # ---------------------------------------------------------
        from datetime import datetime

        appointment_date = datetime.strptime(
            data.get("appointment_date"), "%Y-%m-%d"
            ).date()

        appointment_time = datetime.strptime(
            data.get("appointment_time"), "%I:%M %p"
            ).time()

        if not data.get("appointment_date") or not data.get("appointment_time"):
            return Response({"error": "Appointment date and time are required."}, status=400)

        try:
            appointment_date = datetime.strptime(data.get("appointment_date"), "%Y-%m-%d").date()
            appointment_time = datetime.strptime(data.get("appointment_time"), "%I:%M %p").time()
        except ValueError:
            return Response({"error": "Invalid date or time format"}, status=400)
        # ---------------------------------------------------------
        # STEP 4: Consultation Mode Logic
        # ---------------------------------------------------------
        mode = data.get("mode")

        if doctor.in_clinic:
            mode = "in_clinic"
        elif doctor.e_consultation:
            if not mode:
                return Response({"error": "Mode is required (tele)."}, status=400)
            if mode != "tele":
                return Response({"error": "Doctor only supports tele consultation."}, status=400)
        else:
            return Response({"error": "Doctor has no consultation mode"}, status=400)

        # ---------------------------------------------------------
        # STEP 5: Slot Check (based on existing CartItems!)
        # ---------------------------------------------------------
        slot_in_cart = CartItem.objects.filter(
            user=user,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            item_type="doctor_appointment"
        ).exists()

        if slot_in_cart:
            return Response(
                {"error": f"Slot already added to cart for {doctor.doctor.full_name} "
                          f"on {appointment_date} at {appointment_time}."},
                status=400
            )

        # ---------------------------------------------------------
        # STEP 6: Get or Create Cart
        # ---------------------------------------------------------
        cart, _ = Cart.objects.get_or_create(user=user)

        # ---------------------------------------------------------
        # STEP 7: Create CartItem (NOT Appointment)
        # ---------------------------------------------------------
        price= doctor.consultation_fee
        discount_amount=0
        final_price= price-discount_amount

        cart_item = CartItem.objects.create(
            cart=cart,
            user=user,
            item_type="doctor_appointment",
            symptoms=data.get("symptoms"),

            doctor=doctor,
            specialization=specialization,

            for_whom=for_whom,
            dependant=dependant,

            patient_name=(
                 user.name or user.email
                if for_whom == "self" else dependant.name
            ),

            appointment_date=appointment_date,
            appointment_time=appointment_time,
            mode=mode,

            note=data.get("note"),

            consultation_fee = doctor.consultation_fee, 
            price=price,
            discount_amount=discount_amount,
            final_price=final_price,
            slot_confirmed=True,  
            
            created_by=user,
            updated_by=user
        )



        # ---------------------------------------------------------
        # STEP 8: Upload Documents to CartItem (NOT APPOINTMENT)
        # ---------------------------------------------------------
        for f in request.FILES.getlist("documents"):
            doc = ReportDocument.objects.create(file=f)
            cart_item.documents.add(doc)

        # ---------------------------------------------------------
        # STEP 9: Return Response
        # ---------------------------------------------------------
        return Response(
            {
                "message": "Appointment added to cart",
                "data": DoctorAppointmentToCartSerializer(cart_item, context={"request":request , "doctor_obj":doctor}).data
            },
            status=status.HTTP_201_CREATED
        )



# DENTAL AND EYE APPOINTMENTS-----

# class DentalAppointmentToCartAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         data = request.data.copy()
#         user = request.user

#         # ---------------------------------------------------------
#         # STEP 1: Fixed specialization for Dental
#         # ---------------------------------------------------------
#         specialization = get_object_or_404(DoctorSpeciality, name__iexact="Dentist")

#         # ---------------------------------------------------------
#         # STEP 2: For whom (self / dependant)
#         # ---------------------------------------------------------
#         for_whom = data.get("for_whom")
#         if for_whom not in ["self", "dependant"]:
#             return Response({"error": "for_whom must be 'self' or 'dependant'."}, status=400)

#         dependant = None
#         if for_whom == "dependant":
#             dependant_id = data.get("dependant_id")
#             if not dependant_id:
#                 return Response({"error": "dependant_id is required"}, status=400)
#             dependant = get_object_or_404(Dependant, id=dependant_id, user=user)


#         consultation_fee = data.get("consultation_fee")
#         if not consultation_fee:
#             return Response({"error": "consultation_fee is required"}, status=400)


#         # ---------------------------------------------------------
#         # STEP 3: Validate vendor center
#         # ---------------------------------------------------------
#         center_id = data.get("dental_vendor_center_id")
#         if not center_id:
#             return Response({"error": "dental_vendor_center_id is required"}, status=400)

#         vendor_center = get_object_or_404(DentalVendorAddress, id=center_id)
#         vendor = vendor_center.vendor


#         consultation_fee = Decimal(
#             data.get("consultation_fee") or vendor_center.consultation_fee
#         )
#         # ---------------------------------------------------------
#         # STEP 4: Validate date & time
#         # ---------------------------------------------------------
#         from datetime import datetime

#         appointment_date = datetime.strptime(
#             data.get("appointment_date"), "%Y-%m-%d"
#             ).date()

#         appointment_time = datetime.strptime(
#             data.get("appointment_time"), "%I:%M %p"
#             ).time()

#         if not data.get("appointment_date") or not data.get("appointment_time"):
#             return Response({"error": "Appointment date and time are required."}, status=400)

#         try:
#             appointment_date = datetime.strptime(data.get("appointment_date"), "%Y-%m-%d").date()
#             appointment_time = datetime.strptime(data.get("appointment_time"), "%I:%M %p").time()
#         except ValueError:
#             return Response({"error": "Invalid date or time format"}, status=400)
#         # ---------------------------------------------------------
#         # STEP 5: Slot Check (inside cart only)
#         # ---------------------------------------------------------
#         slot_in_cart = CartItem.objects.filter(
#             user=user,
#             dental_vendor_centers=vendor_center,
#             appointment_date=appointment_date,
#             appointment_time=appointment_time,
#             item_type="dental_appointment"
#         ).exists()

#         if slot_in_cart:
#             return Response(
#                 {"error": f"Slot already added to cart at {vendor_center.address} "
#                           f"on {appointment_date} at {appointment_time}"},
#                 status=400
#             )

#         # ---------------------------------------------------------
#         # STEP 6: Get or create cart
#         # ---------------------------------------------------------
#         cart, _ = Cart.objects.get_or_create(user=user)

#         # ---------------------------------------------------------
#         # STEP 7: Create CartItem (NO Appointment model)
#         # ---------------------------------------------------------

#         price= vendor_center.consultation_fee
#         discount_amount=0
#         final_price= price-discount_amount



#         cart_item = CartItem.objects.create(
#             cart=cart,
#             user=user,
#             item_type="dental_appointment",

#             vendor=vendor,
#             dental_vendor_centers=vendor_center,
#             specialization=specialization,

#             for_whom=for_whom,
#             dependant=dependant,

#             patient_name=(
#                 user.name or user.email
#                 if for_whom == "self" else dependant.name
#             ),

#             appointment_date=appointment_date,
#             appointment_time=appointment_time,
#             note=data.get("note"),
#             mode="In Person",
#             slot_confirmed=True, 
#             price=price,
#             discount_amount=0,
#             final_price=final_price,

            
#             created_by=user,
#             updated_by=user
#         )

#         # ---------------------------------------------------------
#         # STEP 8: Add documents to cart item
#         # ---------------------------------------------------------
#         for f in request.FILES.getlist("documents"):
#             doc = ReportDocument.objects.create(file=f)
#             cart_item.documents.add(doc)

#         return Response(
#             {
#                 "message": "Dental appointment added to cart",
#                 "data": DentalAppointmentToCartSerializer(cart_item).data
#             },
#             status=201
#         )



# class EyeAppointmentToCartAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         data = request.data.copy()
#         user = request.user

#         # ---------------------------------------------------------
#         # STEP 1: Fixed specialization for Eye
#         # ---------------------------------------------------------
#         specialization = get_object_or_404(DoctorSpeciality, name__iexact="Dermatology")

#         # ---------------------------------------------------------
#         # STEP 2: For whom (self / dependant)
#         # ---------------------------------------------------------
#         for_whom = data.get("for_whom")
#         if for_whom not in ["self", "dependant"]:
#             return Response({"error": "for_whom must be 'self' or 'dependant'."}, status=400)

#         dependant = None
#         if for_whom == "dependant":
#             dependant_id = data.get("dependant_id")
#             if not dependant_id:
#                 return Response({"error": "dependant_id is required"}, status=400)
#             dependant = get_object_or_404(Dependant, id=dependant_id, user=user)

#         consultation_fee = data.get("consultation_fee")
#         if not consultation_fee:
#             return Response({"error": "consultation_fee is required"}, status=400)


#         # ---------------------------------------------------------
#         # STEP 3: Validate vendor center
#         # ---------------------------------------------------------
#         center_id = data.get("eye_vendor_centers_id")
#         if not center_id:
#             return Response({"error": "eye_vendor_center_id is required"}, status=400)

#         vendor_center = get_object_or_404(EyeVendorAddress, id=center_id)
#         vendor = vendor_center.vendor

#         consultation_fee = Decimal(
#             data.get("consultation_fee") or vendor_center.consultation_fee
#         ) 

#         # ---------------------------------------------------------
#         # STEP 4: Validate date & time
#         # ---------------------------------------------------------
#         from datetime import datetime

#         appointment_date = datetime.strptime(
#             data.get("appointment_date"), "%Y-%m-%d"
#             ).date()

#         appointment_time = datetime.strptime(
#             data.get("appointment_time"), "%I:%M %p"
#             ).time()

#         if not data.get("appointment_date") or not data.get("appointment_time"):
#             return Response({"error": "Appointment date and time are required."}, status=400)

#         try:
#             appointment_date = datetime.strptime(data.get("appointment_date"), "%Y-%m-%d").date()
#             appointment_time = datetime.strptime(data.get("appointment_time"), "%I:%M %p").time()
#         except ValueError:
#             return Response({"error": "Invalid date or time format"}, status=400)

#         # ---------------------------------------------------------
#         # STEP 5: Slot Check (inside cart only)
#         # ---------------------------------------------------------
#         slot_in_cart = CartItem.objects.filter(
#             user=user,
#             eye_vendor_centers=vendor_center,
#             appointment_date=appointment_date,
#             appointment_time=appointment_time,
#             item_type="eye_appointment"
#         ).exists()

#         if slot_in_cart:
#             return Response(
#                 {"error": f"Slot already added to cart at {vendor_center.address} "
#                           f"on {appointment_date} at {appointment_time}"},
#                 status=400
#             )

#         # ---------------------------------------------------------
#         # STEP 6: Get or create cart
#         # ---------------------------------------------------------
#         cart, _ = Cart.objects.get_or_create(user=user)

    
#         # ---------------------------------------------------------
#         # STEP 7: Create CartItem (NO Appointment model)
#         # ---------------------------------------------------------

#         price= vendor_center.consultation_fee
#         discount_amount=0
#         final_price= price-discount_amount


#         cart_item = CartItem.objects.create(
#             cart=cart,
#             user=user,
#             item_type="eye_appointment",

#             vendor=vendor,
#             eye_vendor_centers=vendor_center,
#             specialization=specialization,

#             for_whom=for_whom,
#             dependant=dependant,
#             mode="In Person",
#             patient_name=(
#                 user.name or user.email
#                 if for_whom == "self" else dependant.name
#             ),

#             appointment_date=appointment_date,
#             appointment_time=appointment_time,
#             note=data.get("note"),
#             price=price,
#             discount_amount=0,
#             final_price=final_price,
#             slot_confirmed=True,  

#             created_by=user,
#             updated_by=user
#         )

#         # ---------------------------------------------------------
#         # STEP 8: Add documents
#         # ---------------------------------------------------------
#         for f in request.FILES.getlist("documents"):
#             doc = ReportDocument.objects.create(file=f)
#             cart_item.documents.add(doc)

#         return Response(
#             {
#                 "message": "Eye appointment added to cart",
#                 "data": EyeAppointmentToCartSerializer(cart_item).data
#             },
#             status=201
#         )
    


class RescheduleAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, cart_item_id):
        user = request.user
        data = request.data

        # 1. Get cart item
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=user)

        # 2. Parse new date/time
        from datetime import datetime

        new_date_str = data.get("appointment_date")
        new_time_str = data.get("appointment_time")

        if not new_date_str or not new_time_str:
            return Response({"error": "appointment_date and appointment_time are required"}, status=400)

        try:
            new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
            new_time = datetime.strptime(new_time_str, "%I:%M %p").time()
        except ValueError:
            return Response({"error": "Invalid date or time format"}, status=400)

        # 3. Slot check (avoid double booking)
        slot_exists = CartItem.objects.filter(
            user=user,
            doctor=cart_item.doctor,
            appointment_date=new_date,
            appointment_time=new_time,
            item_type=cart_item.item_type
        ).exclude(id=cart_item.id).exists()

        if slot_exists:
            return Response(
                {"error": f"Slot already booked on {new_date} at {new_time}"},
                status=400
            )

        # 4. Update the cart item
        cart_item.appointment_date = new_date
        cart_item.appointment_time = new_time
        cart_item.updated_by = user
        cart_item.save()

        # 5. Return updated response
        return Response(
            {
                "message": "Appointment rescheduled successfully",
                "data": DoctorAppointmentToCartSerializer(
                    cart_item,
                    context={"request": request, "doctor_obj": cart_item.doctor}
                ).data
            },
            status=200
        )


class RemoveCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({"detail": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response({"detail": "Item removed."}, status=status.HTTP_200_OK)


class ClearCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({"detail": "Cart cleared."}, status=status.HTTP_200_OK)



class AvailableLabSlotsAPIView(APIView):

    def get(self, request, center_id, date):
        # parse date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format, expected YYYY-MM-DD"}, status=400)

        center = get_object_or_404(DiagnosticCenter, id=center_id)

        slots = generate_time_slots_for_center(center, date_obj)
        result = []
        for s in slots:
            start_time = s["start_time"]
            booked = get_slot_booked_count(center.id, date_obj, start_time)
            available = max(0, (center.slot_capacity or 1) - booked)


            slot_dt = timezone.make_aware(
                      datetime.combine(date_obj, start_time),
                      timezone.get_current_timezone()
                      )


            result.append({
                "start_time": start_time.strftime("%I:%M %p"),
                "end_time": s["end_time"].strftime("%I:%M %p"),
                "capacity": center.slot_capacity,
                "booked": booked,
                "available": available,
      
                "is_past": slot_dt < timezone.now()

            })

        return Response({
            "center_id": center.id,
            "date": date_obj.isoformat(),
            "slots": result
        })



# class SelectLabSlotAPIView(APIView):

#     def post(self, request, cart_item_id):
#         try:
#             item = CartItem.objects.get(id=cart_item_id, cart__user=request.user)
#         except CartItem.DoesNotExist:
#             return Response({"error": "Cart item not found"}, status=404)

#         # Allowed item types
#         ALLOWED_TYPES = ["test", "health_package", "sponsored_package"]

#         if item.item_type not in ALLOWED_TYPES:
#             return Response(
#                 {"error": "Slot selection allowed only for Test, Health Package, and Sponsored Package"},
#                 status=400
#             )

#         date_str = request.data.get("date")
#         time_str = request.data.get("time")

#         if not date_str or not time_str:
#             return Response({"error": "Both date and time are required"}, status=400)

#         # Convert date
#         try:
#             date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
#         except:
#             return Response({"error": "Invalid date format"}, status=400)

#         # Convert time
#         try:
#             time_obj = datetime.strptime(time_str, "%I:%M %p").time()
#         except:
#             return Response({"error": "Invalid time format"}, status=400)

#         # Past date check
#         if date_obj < date.today():
#             return Response({"error": "You cannot select past dates"}, status=400)

#         # Business hours: 7AM to 7PM
#         if time_obj < time(7, 0) or time_obj > time(19, 0):
#             return Response({"error": "Time must be between 7 AM and 7 PM"}, status=400)

#         # All share the same diagnostic center
#         center = item.diagnostic_center
#         if not center:
#             return Response({"error": "Diagnostic center not assigned"}, status=400)

#         # Generate available slots
#         slots = generate_time_slots_for_center(center, date_obj)
#         slot_times = [s["start_time"] for s in slots]

#         if time_obj not in slot_times:
#             return Response({"error": "Selected time not available for this center"}, status=400)

#         # ----------------------------------------------------
#         # GENERALIZED SLOT COUNT CHECK (FOR ALL ITEM TYPES)
#         # ----------------------------------------------------
#         with transaction.atomic():

#             booked = CartItem.objects.filter(
#                 diagnostic_center=center,
#                 selected_date=date_obj,
#                 selected_time=time_obj,
#                 slot_confirmed=True
#             ).count()

#             capacity = center.slot_capacity or 1

#             if booked >= capacity:
#                 return Response({"error": "Selected slot is fully booked"}, status=400)

#         # Save the slot
#         item.selected_date = date_obj
#         item.selected_time = time_obj
#         item.slot_confirmed = True
#         item.save()

#         return Response({
#             "message": "Slot selected successfully",
#             "cart_item_id": item.id,
#             "item_type": item.item_type,
#             "selected_date": item.selected_date.isoformat(),
#             "selected_time": item.selected_time.strftime("%I:%M %p")
#         }, status=200)

# class RescheduleLabSlotAPIView(APIView):

#     def post(self, request, cart_item_id):
#         try:
#             item = CartItem.objects.select_related("diagnostic_center").get(
#                 id=cart_item_id,
#                 cart__user=request.user
#             )
#         except CartItem.DoesNotExist:
#             return Response({"error": "Cart item not found"}, status=404)

#         # Allowed item types
#         ALLOWED_TYPES = ["test", "health_package", "sponsored_package"]

#         if item.item_type not in ALLOWED_TYPES:
#             return Response(
#                 {"error": "Only test, health package & sponsored package items support rescheduling"},
#                 status=400
#             )

#         # Must have an existing slot to reschedule
#         if not item.selected_date or not item.selected_time:
#             return Response({"error": "Item has no existing slot selected"}, status=400)

#         # Extract new date & time
#         date_str = request.data.get("date")
#         time_str = request.data.get("time")

#         if not date_str or not time_str:
#             return Response({"error": "date and time are required"}, status=400)

#         try:
#             new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#             new_time = datetime.strptime(time_str, "%I:%M %p").time()
#         except ValueError:
#             return Response({"error": "Invalid date/time format"}, status=400)

#         center = item.diagnostic_center
#         if not center:
#             return Response({"error": "Diagnostic center not assigned"}, status=400)

#         # Generate valid slots for this center
#         slots = generate_time_slots_for_center(center, new_date)
#         slot_times = [s["start_time"] for s in slots]

#         if new_time not in slot_times:
#             return Response({"error": "Selected time not available for this center"}, status=400)

#         # If user picked the same date/time → nothing to update
#         if item.selected_date == new_date and item.selected_time == new_time:
#             return Response({"message": "No change"}, status=200)

#         # Concurrency-safe booking block
#         with transaction.atomic():

#             # Count already booked items for this slot
#             booked = CartItem.objects.filter(
#                 diagnostic_center=center,
#                 selected_date=new_date,
#                 selected_time=new_time,
#                 slot_confirmed=True
#             ).count()

#             # If the item already occupies this slot, subtract it once
#             # (allows rescheduling back to same slot safely)
#             if item.selected_date == new_date and item.selected_time == new_time:
#                 booked = max(0, booked - 1)

#             capacity = center.slot_capacity or 1

#             if booked >= capacity:
#                 return Response({"error": "Selected new slot is fully booked"}, status=400)

#             # Update slot
#             item.selected_date = new_date
#             item.selected_time = new_time
#             item.slot_confirmed = True
#             item.save()

#         return Response({
#             "message": "Slot rescheduled successfully",
#             "cart_item_id": item.id,
#             "item_type": item.item_type,
#             "selected_date": item.selected_date.isoformat(),
#             "selected_time": item.selected_time.strftime("%H:%M")
#         })



# class CartViewSet(viewsets.ReadOnlyModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = CartItemListSerializer

#     def get_queryset(self):
#         return CartItem.objects.filter(
#             user=self.request.user,
#             deleted_at__isnull=True
#         )


# VOUCHER CREATION-------

class CreateAppointmentVoucherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        user = request.user

        # 1. Get cart item
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            user=user,
            item_type="doctor_appointment"
        )

        # 2. Prevent duplicate voucher creation
        if hasattr(appointment, "voucher"):
            return Response(
                {"error": "Voucher already created for this appointment"},
                status=400
            )

        # 3. Create Voucher (ONLY voucher, no appointment)
        voucher = AppointmentVoucher.objects.create(
            appointment=appointment
        )

        return Response(
            {
                "message": "Voucher created successfully",
                "voucher":AppointmentVoucherSerializer(voucher).data
                # "voucher_id": voucher.id,
                # "voucher_details": {
                #     "doctor": appointment.doctor.doctor.full_name,
                #     "appointment_date": str(appointment.appointment_date),
                #     "appointment_time": str(appointment.appointment_time),
                #     "mode": appointment.mode,
                # }
            },
            status=201
        )
