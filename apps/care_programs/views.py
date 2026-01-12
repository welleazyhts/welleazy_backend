# apps/care_programs/views.py
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
from apps.common.utils.profile_helper import filter_by_effective_user
from .models import CareProgramBooking
from .serializers import (
    CareProgramBookingSerializer,
    CareProgramBookingPayloadSerializer,
)
from apps.notifications.utils import notify_user

class CareProgramBookingViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CareProgramBookingSerializer
    queryset = CareProgramBooking.objects.all()

    def get_queryset(self):
        queryset = CareProgramBooking.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True,
        ).order_by("-created_at")
        return filter_by_effective_user(queryset, self.request)

    # CREATE
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = CareProgramBookingPayloadSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        # Create Booking Instance
        booking = CareProgramBooking(
            user=request.user,
            created_by=request.user,
            updated_by=request.user,
        )

        self._save_booking_fields(booking, payload.validated_data, request)

        request_type = request.data.get("request_type")

        if request_type == "callback":
            booking.status = "callback_requested"  
        else:
            booking.status = "pending"              

        booking.save()

        if request_type == "callback":

            notify_user(
                request.user,
                "Callback Requested",
                f"We recieved your callback request for {booking.service_type} . Our care team will contact you soon."
            )
            return Response(
                {
                    "message": "Callback request submitted. Our team will contact you shortly.",
                    "booking": CareProgramBookingSerializer(booking).data,
                },
                status=status.HTTP_201_CREATED,
            )
        

        notify_user(
            request.user,
            "Care Program Booked",
            f"Your {booking.service_type} care program has been booked successfully.",
            item_type="care_program"
        )
        return Response(
            {
                "message": "Care program booked successfully",
                "data": CareProgramBookingSerializer(booking).data,
            },
            status=status.HTTP_201_CREATED,
        )


    # UPDATE
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        booking = self.get_object()

        payload = CareProgramBookingPayloadSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        booking.updated_by = request.user
        self._save_booking_fields(booking, payload.validated_data, request)
        booking.save()

        return Response(
            {
                "message": "Booking updated successfully",
                "data": CareProgramBookingSerializer(booking).data
            },
            status=status.HTTP_200_OK
        )
    # SOFT DELETE
    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        booking.deleted_at = timezone.now()
        booking.save()
        return Response(
            {"message": "Booking deleted successfully"},
            status=status.HTTP_200_OK
        )
    # OPTIONS (SELF + DEPENDANTS)
    @action(detail=False, methods=["get"], url_path="options")
    def booking_options(self, request):

        service_type = request.query_params.get("service_type")
        allowed = [c[0] for c in CareProgramBooking.SERVICE_TYPE_CHOICES]

        if not service_type or service_type not in allowed:
            return Response(
                {"detail": "Invalid or missing service_type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        options = []

        # Self
        self_home = self._get_default_home_address_for_user(user)
        options.append({
            "for_whom": "self",
            "dependant_id": None,
            "person_name": user.name,
            "relationship": "Self",
            "service_type": service_type,
            "contact_number": user.mobile_number,
            "email": user.email,
            "address": AddressSerializer(self_home).data if self_home else None,
            "requirements": "",
        })

        # Dependants
        for dep in Dependant.objects.filter(user=user, is_active=True):
            dep_home = self._get_default_home_address_for_dependant(dep)
            options.append({
                "for_whom": "dependant",
                "dependant_id": dep.id,
                "person_name": dep.name,
                "relationship": dep.relationship.name if dep.relationship else None,
                "service_type": service_type,
                "contact_number": user.mobile_number,
                "email": user.email,
                "address": AddressSerializer(dep_home).data if dep_home else None,
                "requirements": "",
            })

        return Response({"service_type": service_type, "options": options})


    def _save_booking_fields(self, booking, validated, request):
        user = request.user

        # Basic fields
        booking.for_whom = validated["for_whom"]
        booking.service_type = validated["service_type"]
        booking.requirements = validated.get("requirements", "")

        # Handle dependant vs self
        dependant_id = validated.get("dependant")
        if booking.for_whom == "dependant":
            dep = Dependant.objects.get(id=dependant_id, user=user, is_active=True)
            booking.dependant = dep
            booking.name = dep.name
            booking.email = user.email
            booking.contact_number = user.mobile_number
        else:
            booking.dependant = None
            booking.name = user.name
            booking.email = user.email
            booking.contact_number = user.mobile_number

        # CASE A: User selected a saved address explicitly
        addr_id = validated.get("address")
        if addr_id:
            try:
                addr = Address.objects.select_related("state", "city").get(
                    id=addr_id,
                    is_active=True,
                    user=user if booking.for_whom == "self" else None,
                    dependant=booking.dependant if booking.for_whom == "dependant" else None,
                )
            except Address.DoesNotExist:
                raise ValidationError({"address": "Invalid address for this person."})

            booking.address = addr
            booking.state = addr.state
            booking.city = addr.city
            booking.address_text = addr.address_line1 + ", " + (addr.address_line2 or "") + ", " + (addr.landmark or "") + "-" + addr.pincode
            return

        # CASE B: Manual address provided -> PRIORITY over default
        if validated.get("state") or validated.get("city") or validated.get("address_text"):
            state_obj = State.objects.filter(id=validated.get("state")).first()
            city_obj = City.objects.filter(id=validated.get("city")).first()

            booking.address = None
            booking.state = state_obj
            booking.city = city_obj
            booking.address_text = validated.get("address_text", "")
            return

        # CASE C: No user input -> fallback to default address
        if booking.for_whom == "self":
            default_addr = self._get_default_home_address_for_user(user)
        else:
            default_addr = self._get_default_home_address_for_dependant(booking.dependant)

        if default_addr:
            booking.address = default_addr
            booking.state = default_addr.state
            booking.city = default_addr.city
            booking.address_text = default_addr.address_line1 + ", " + (default_addr.address_line2 or "") + ", " + (default_addr.landmark or "") + "-" + default_addr.pincode
            return

        # CASE D: No address available at all -> require manual input
        raise ValidationError({
            "address_text": "No address found. Please enter a manual address (state, city, address_text)."
        })



    def _get_default_home_address_for_user(self, user):
        qs = Address.objects.filter(user=user, is_active=True)
        home = qs.filter(address_type__name__iexact="home", is_default=True).first()
        if home:
            return home
        home = qs.filter(address_type__name__iexact="home").first()
        if home:
            return home
        return qs.first()

    def _get_default_home_address_for_dependant(self, dependant):
        qs = Address.objects.filter(dependant=dependant, is_active=True)
        home = qs.filter(address_type__name__iexact="home", is_default=True).first()
        if home:
            return home
        home = qs.filter(address_type__name__iexact="home").first()
        if home:
            return home
        return qs.first()
