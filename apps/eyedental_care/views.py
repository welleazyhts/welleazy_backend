from django.shortcuts import render

# Create your views here.


from rest_framework.viewsets import ModelViewSet
from .models import (
    EyeTreatment, DentalTreatment
)
from .serializers import (
    EyeTreatmentSerializer, DentalTreatmentSerializer
    
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

from rest_framework import viewsets, permissions, status, mixins

from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.common.mixins.save_user_mixin import SaveUserMixin
from apps.dependants.models import Dependant
from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.location.models import State, City

from .models import EyeDentalCareBooking
from .serializers import EyeDentalCareBookingSerializer
from .serializers import EyeDentalCareBookingFinalSerializer


class SmallPagination(PageNumberPagination):
    page_size = 12



class EyeTreatmentViewSet(ModelViewSet):
    queryset = EyeTreatment.objects.all()
    serializer_class = EyeTreatmentSerializer
    pagination_class = SmallPagination


class DentalTreatmentViewSet(ModelViewSet):
    queryset = DentalTreatment.objects.all()
    serializer_class = DentalTreatmentSerializer
    pagination_class = SmallPagination



# class EyeDentalVoucherViewSet(ModelViewSet):
#     queryset = EyeDentalVoucher.objects.all().order_by("-created_at")

#     def get_serializer_class(self):
#         if self.action == "create":
#             return EyeDentalVoucherCreateSerializer
#         return EyeDentalVoucherSerializer
    
#     def get_queryset(self):
#         user = self.request.user
#         if user.is_staff:
#             return EyeDentalVoucher.objects.all()
#         return EyeDentalVoucher.objects.filter(user=user)


#     def retrieve(self, request, *args, **kwargs):
#         voucher = self.get_object()

#         if voucher.user != request.user and not request.user.is_staff:
#             return Response({"detail": "You do not own this voucher"}, status=403)

#         serializer = self.get_serializer(voucher)
#         return Response(serializer.data)


#     @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
#     def activate(self, request, pk=None):
#         voucher = self.get_object()
#         voucher.status = 'active'
#         voucher.activated_at = timezone.now()
#         voucher.save()
#         return Response({'status': 'activated', 'voucher_id': voucher.voucher_id_display()})

#     @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
#     def cancel(self, request, pk=None):
#         voucher = self.get_object()
#         voucher.status = 'cancelled'
#         voucher.save()
#         return Response({'status': 'cancelled'})
    
    
    

class EyeDentalCareBookingViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EyeDentalCareBookingSerializer
    queryset = EyeDentalCareBooking.objects.all()

    def get_queryset(self):
        return EyeDentalCareBooking.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True
        ).order_by("-created_at")

    # ============================================================
    # STEP 1 — SELECT TREATMENT (CREATE DRAFT)
    # ============================================================
    @action(detail=False, methods=["post"], url_path="select-booking-type")
    def select_booking_type(self, request):
        """
        STEP 1:
        After care_program_type is chosen, user selects:
        - treatment
        - OR book_appointment
        """

        care_program_type = request.data.get("care_program_type")
        booking_type = request.data.get("booking_type")

        eye_treatment = request.data.get("eye_treatment")
        dental_treatment = request.data.get("dental_treatment")

        if care_program_type not in ["eye", "dental"]:
            return Response(
                {"care_program_type": "Invalid value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking_type not in ["treatment", "book_appointment"]:
            return Response(
                {"booking_type": "Invalid value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # -------------------------------
    # If booking_type = treatment
    # -------------------------------
        if booking_type == "treatment":
            if care_program_type == "eye" and not eye_treatment:
                return Response(
                    {"eye_treatment": "Eye treatment is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if care_program_type == "dental" and not dental_treatment:
                return Response(
                    {"dental_treatment": "Dental treatment is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    # -------------------------------
    # Create draft booking
    # -------------------------------
        booking = EyeDentalCareBooking.objects.create(
            user=request.user,
            care_program_type=care_program_type,
            booking_type=booking_type,
            eye_treatment_id=eye_treatment if booking_type == "treatment" and care_program_type == "eye" else None,
            dental_treatment_id=dental_treatment if booking_type == "treatment" and care_program_type == "dental" else None,
            status="pending",
        )

        return Response(
            {
                "booking_id": booking.id,
                "care_program_type": booking.care_program_type,
                "booking_type": booking.booking_type,
                "next_step": "select_service_type",
            },
            status=status.HTTP_201_CREATED,
            )


    # ============================================================
    # STEP 2 — SELECT SERVICE TYPE
    # ============================================================
    @action(detail=True, methods=["patch"], url_path="select-service-type")
    def select_service_type(self, request, pk=None):
        booking = self.get_object()

        if booking.status != "pending":
            raise ValidationError("Service type already selected")

        service_type = request.data.get("service_type")
        allowed = [c[0] for c in EyeDentalCareBooking.SERVICE_TYPE_CHOICES]

        if service_type not in allowed:
            raise ValidationError({"service_type": "Invalid value"})

        booking.service_type = service_type
        booking.status = "service_selected"
        booking.save(update_fields=["service_type", "status"])

        return Response(
            {
                "booking_id": booking.id,
                "next_step": "select_for_whom"
            }
        )



    # ============================================================
    # STEP 3 — SELF / DEPENDANT OPTIONS (PREFILL)
    # ============================================================
    @action(detail=False, methods=["get"], url_path="options")
    def booking_options(self, request):
        user = request.user
        options = []

    # =========================
    # SELF
    # =========================
        user_addresses = Address.objects.filter(
            user=user,
            is_active=True
        ).select_related("state", "city", "address_type")

        options.append({
            "for_whom": "self",
            "dependant_id": None,
            "name": user.name,
            "relationship": "Self",
            "addresses": AddressSerializer(user_addresses, many=True).data,
            "allow_manual_address": True,   # 👈 important
        })

    # =========================
    # DEPENDANTS
    # =========================
        for dep in Dependant.objects.filter(user=user, is_active=True):
            dep_addresses = Address.objects.filter(
                dependant=dep,
                is_active=True
            ).select_related("state", "city", "address_type")

            options.append({
                "for_whom": "dependant",
                "dependant_id": dep.id,
                "name": dep.name,
                "relationship": dep.relationship.name if dep.relationship else None,
                "addresses": AddressSerializer(dep_addresses, many=True).data,
                "allow_manual_address": True,   # 👈 important
            })

        return Response({"options": options})


    # ============================================================
    # STEP 4 — FINAL SUBMIT / UPDATE
    # ============================================================
    @action(detail=True, methods=["patch"], url_path="final-submit")
    @transaction.atomic
    def final_submit(self, request, pk=None):
        booking = self.get_object()

        if booking.status != "service_selected":
            raise ValidationError("Complete previous steps first")

        serializer = EyeDentalCareBookingFinalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        self._save_final_fields(booking, data, request)
        booking.status = "confirmed"
        booking.save()

        return Response(
            {
                "message": "Booking confirmed",
                "data": EyeDentalCareBookingSerializer(booking).data
            }
        )


    # ============================================================
    # SOFT DELETE
    # ============================================================
    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        booking.deleted_at = timezone.now()
        booking.save(update_fields=["deleted_at"])
        return Response(
            {"message": "Booking deleted successfully"},
            status=status.HTTP_200_OK,
        )

    # ============================================================
    # COMMON FIELD HANDLER
    # ============================================================
    def _save_final_fields(self, booking, validated, request):
        user = request.user

        booking.for_whom = validated["for_whom"]
        booking.requirements = validated.get("requirements", "")

        if booking.for_whom == "dependant":
            dep = Dependant.objects.get(
                id=validated["dependant"], user=user, is_active=True
            )
            booking.dependant = dep
            booking.name = dep.name
            booking.email = user.email
            booking.contact_number = user.mobile_number
        else:
            booking.dependant = None
            booking.name = user.name
            booking.email = user.email
            booking.contact_number = user.mobile_number

        addr_id = validated.get("address")
        if addr_id:
            addr = Address.objects.select_related("state", "city").filter(
                id=addr_id,
                is_active=True,
                user=user if booking.for_whom == "self" else None,
                dependant=booking.dependant if booking.for_whom == "dependant" else None,
            ).first()

            if not addr:
                raise ValidationError({"address": "Invalid address"})

            booking.address = addr
            booking.state = addr.state
            booking.city = addr.city
            booking.address_text = f"{addr.address_line1}, {addr.pincode}"
            return

        if validated.get("state") or validated.get("city") or validated.get("address_text"):
            booking.address = None
            booking.state = State.objects.filter(id=validated.get("state")).first()
            booking.city = City.objects.filter(id=validated.get("city")).first()
            booking.address_text = validated.get("address_text", "")
            return

        default_addr = (
            self._get_default_home_address_for_user(user)
            if booking.for_whom == "self"
            else self._get_default_home_address_for_dependant(booking.dependant)
        )

        if default_addr:
            booking.address = default_addr
            booking.state = default_addr.state
            booking.city = default_addr.city
            booking.address_text = f"{default_addr.address_line1}, {default_addr.pincode}"
            return

        raise ValidationError(
            {"address_text": "Please provide address details"}
        )

    # ============================================================
    # DEFAULT ADDRESS HELPERS
    # ============================================================
    def _get_default_home_address_for_user(self, user):
        qs = Address.objects.filter(user=user, is_active=True)
        return (
            qs.filter(address_type__name__iexact="home", is_default=True).first()
            or qs.filter(address_type__name__iexact="home").first()
            or qs.first()
        )

    def _get_default_home_address_for_dependant(self, dependant):
        qs = Address.objects.filter(dependant=dependant, is_active=True)
        return (
            qs.filter(address_type__name__iexact="home", is_default=True).first()
            or qs.filter(address_type__name__iexact="home").first()
            or qs.first()
        )



