from rest_framework import serializers
from .models import (
    EyeDentalService,
    EyeTreatment, DentalTreatment,
    EyeVendorAddress, DentalVendorAddress,
    EyeDentalVoucher, EyeDentalVoucherRemark
)
from apps.dependants.models import Dependant


# ---------------------------------------
#  SERVICE PROGRAM SERIALIZERS
# ---------------------------------------
class EyeDentalServiceSerializer(serializers.ModelSerializer):
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)

    class Meta:
        model = EyeDentalService
        fields = [
            "id", "name", "service_type", "service_type_display",
            "description", "detailed_description", "image",
            "display_order", "is_active"
        ]


# ---------------------------------------
#  TREATMENT SERIALIZERS
# ---------------------------------------
class EyeTreatmentSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source='short_description', read_only=True)

    class Meta:
        model = EyeTreatment
        fields = ["id", "name", "description", "detailed_description", "image", "is_active"]


class DentalTreatmentSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source='short_description', read_only=True)

    class Meta:
        model = DentalTreatment
        fields = ["id", "name", "description", "detailed_description", "image", "is_active"]


# ---------------------------------------
#  VENDOR SERIALIZERS
# ---------------------------------------
class EyeVendorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    city_id = serializers.IntegerField(source='city.id', read_only=True)
    state = serializers.SerializerMethodField()
    state_id = serializers.IntegerField(source='state.id', read_only=True)
    treatments = EyeTreatmentSerializer(many=True, read_only=True)

    class Meta:
        model = EyeVendorAddress
        fields = [
            "id", "name", "address", "city", "city_id", "state", "state_id", "pincode",
            "phone", "email", "consultation_fee", "treatments", "is_active"
        ]

    def get_name(self, obj):
        return obj.name or obj.vendor.name

    def get_city(self, obj):
        return obj.city.name if obj.city else None

    def get_state(self, obj):
        return obj.state.name if obj.state else None


class DentalVendorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    city_id = serializers.IntegerField(source='city.id', read_only=True)
    state = serializers.SerializerMethodField()
    state_id = serializers.IntegerField(source='state.id', read_only=True)
    treatments = DentalTreatmentSerializer(many=True, read_only=True)

    class Meta:
        model = DentalVendorAddress
        fields = [
            "id", "name", "address", "city", "city_id", "state", "state_id", "pincode",
            "phone", "email", "consultation_fee", "treatments", "is_active"
        ]

    def get_name(self, obj):
        return obj.name or obj.vendor.name

    def get_city(self, obj):
        return obj.city.name if obj.city else None

    def get_state(self, obj):
        return obj.state.name if obj.state else None


# ---------------------------------------
#  VOUCHER REMARK SERIALIZERS
# ---------------------------------------
class EyeDentalVoucherRemarkSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EyeDentalVoucherRemark
        fields = ["id", "voucher", "remark", "created_by", "created_by_name", "created_at"]
        read_only_fields = ["created_by", "created_at"]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return None


# ---------------------------------------
#  VOUCHER SERIALIZERS
# ---------------------------------------
class EyeDentalVoucherCreateSerializer(serializers.ModelSerializer):
    voucher_type = serializers.CharField(source='service_type')
    for_dependant = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = EyeDentalVoucher
        fields = [
            "voucher_type",
            "eye_treatment",
            "dental_treatment",
            "eye_vendor",
            "dental_vendor",
            "for_dependant",
        ]

    def validate(self, data):
        service_type = data.get("service_type")

        # Validate for EYE CARE
        if service_type == "eye":
            if not data.get("eye_vendor"):
                raise serializers.ValidationError("eye_vendor is required for Eye Care.")

        # Validate for DENTAL CARE
        if service_type == "dental":
            if not data.get("dental_vendor"):
                raise serializers.ValidationError("dental_vendor is required for Dental Care.")

        return data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        dependant_name = None
        dependant_relationship = None
        dependant_id = None
        booking_for = "self"
        for_dependant = validated_data.pop("for_dependant", None)

        if for_dependant:
            try:
                dependant_obj = Dependant.objects.get(id=for_dependant, user=user)
                dependant_name = dependant_obj.name
                dependant_relationship = dependant_obj.relationship
                dependant_id = dependant_obj.id
                booking_for = "dependant"
            except Dependant.DoesNotExist:
                pass

        # Get user details for voucher
        name = user.name if hasattr(user, 'name') else user.get_full_name() or user.email
        contact_number = user.phone if hasattr(user, 'phone') else ""
        email = user.email

        # Get corporate info if available
        corporate_id = getattr(user, 'corporate_id', None)
        corporate_branch_id = getattr(user, 'corporate_branch_id', None)

        voucher = EyeDentalVoucher.objects.create(
            user=user,
            corporate_id=corporate_id,
            corporate_branch_id=corporate_branch_id,
            booking_for=booking_for,
            dependant_name=dependant_name,
            dependant_relationship=dependant_relationship,
            dependant_id=dependant_id,
            service_type=validated_data.get("service_type"),
            eye_treatment=validated_data.get("eye_treatment"),
            dental_treatment=validated_data.get("dental_treatment"),
            eye_vendor=validated_data.get("eye_vendor"),
            dental_vendor=validated_data.get("dental_vendor"),
            name=dependant_name or name,
            contact_number=contact_number,
            email=email,
            state="",
            city="",
            address="",
        )

        return voucher


class EyeDentalVoucherSerializer(serializers.ModelSerializer):
    voucher_id = serializers.CharField(source='request_id', read_only=True)
    voucher_type = serializers.CharField(source='service_type', read_only=True)
    service_name = serializers.SerializerMethodField()
    treatment_name = serializers.SerializerMethodField()
    vendor_name = serializers.SerializerMethodField()
    center_address = serializers.SerializerMethodField()
    eye_vendor = EyeVendorSerializer(read_only=True)
    dental_vendor = DentalVendorSerializer(read_only=True)
    eye_treatment = EyeTreatmentSerializer(read_only=True)
    dental_treatment = DentalTreatmentSerializer(read_only=True)
    for_dependant = serializers.SerializerMethodField()
    remarks = EyeDentalVoucherRemarkSerializer(many=True, read_only=True)

    class Meta:
        model = EyeDentalVoucher
        fields = [
            "id",
            "voucher_id",
            "voucher_type",
            "user",
            "eye_vendor",
            "dental_vendor",
            "eye_treatment",
            "dental_treatment",
            "for_dependant",
            "dependant_name",
            "dependant_relationship",
            "status",
            "appointment_date",
            "appointment_time",
            "activated_at",
            "service_name",
            "treatment_name",
            "vendor_name",
            "center_address",
            "vendor_name_snapshot",
            "vendor_address_snapshot",
            "service_name_snapshot",
            "treatment_name_snapshot",
            "name",
            "contact_number",
            "email",
            "state",
            "city",
            "address",
            "comment",
            "remarks",
            "created_at",
            "updated_at",
        ]

    def get_for_dependant(self, obj):
        return obj.booking_for == "dependant"

    def get_vendor_name(self, obj):
        # First check snapshot, then live data
        if obj.vendor_name_snapshot:
            return obj.vendor_name_snapshot
        if obj.service_type == "eye" and obj.eye_vendor:
            return obj.eye_vendor.name or obj.eye_vendor.vendor.name
        if obj.service_type == "dental" and obj.dental_vendor:
            return obj.dental_vendor.name or obj.dental_vendor.vendor.name
        return None

    def get_center_address(self, obj):
        # First check snapshot, then live data
        if obj.vendor_address_snapshot:
            return obj.vendor_address_snapshot
        if obj.service_type == "eye" and obj.eye_vendor:
            return obj.eye_vendor.address
        if obj.service_type == "dental" and obj.dental_vendor:
            return obj.dental_vendor.address
        return None

    def get_service_name(self, obj):
        if obj.service_name_snapshot:
            return obj.service_name_snapshot
        return "Eye Care" if obj.service_type == "eye" else "Dental Care"

    def get_treatment_name(self, obj):
        # First check snapshot, then live data
        if obj.treatment_name_snapshot:
            return obj.treatment_name_snapshot
        if obj.service_type == "eye" and obj.eye_treatment:
            return obj.eye_treatment.name
        if obj.service_type == "dental" and obj.dental_treatment:
            return obj.dental_treatment.name
        return None


# ---------------------------------------
#  ADMIN SERIALIZERS
# ---------------------------------------
class EyeDentalVoucherAdminSerializer(serializers.ModelSerializer):
    """Admin serializer with full case details and update capability"""
    voucher_id = serializers.CharField(source='request_id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    eye_treatment_name = serializers.CharField(source='eye_treatment.name', read_only=True)
    dental_treatment_name = serializers.CharField(source='dental_treatment.name', read_only=True)
    remarks = EyeDentalVoucherRemarkSerializer(many=True, read_only=True)

    class Meta:
        model = EyeDentalVoucher
        fields = [
            "id",
            "voucher_id",
            "user",
            "user_email",
            "corporate_id",
            "corporate_branch_id",
            "booking_for",
            "dependant_name",
            "dependant_relationship",
            "dependant_id",
            "service_type",
            "status",
            "eye_treatment",
            "eye_treatment_name",
            "dental_treatment",
            "dental_treatment_name",
            "eye_vendor",
            "dental_vendor",
            "vendor_name_snapshot",
            "vendor_address_snapshot",
            "service_name_snapshot",
            "treatment_name_snapshot",
            "appointment_date",
            "appointment_time",
            "activated_at",
            "name",
            "contact_number",
            "email",
            "state",
            "city",
            "address",
            "comment",
            "updated_by",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ['request_id', 'created_at', 'updated_at']


class EyeDentalVoucherAdminUpdateSerializer(serializers.ModelSerializer):
    """Admin serializer for updating case status and remarks"""
    add_remark = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = EyeDentalVoucher
        fields = [
            "status",
            "appointment_date",
            "appointment_time",
            "eye_treatment",
            "dental_treatment",
            "eye_vendor",
            "dental_vendor",
            "vendor_name_snapshot",
            "vendor_address_snapshot",
            "service_name_snapshot",
            "treatment_name_snapshot",
            "comment",
            "add_remark",
        ]

    def update(self, instance, validated_data):
        request = self.context.get('request')
        add_remark = validated_data.pop('add_remark', None)

        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Set updated_by if request user is available
        if request and request.user:
            instance.updated_by = request.user

        instance.save()

        # Add remark if provided
        if add_remark and request and request.user:
            EyeDentalVoucherRemark.objects.create(
                voucher=instance,
                remark=add_remark,
                created_by=request.user
            )

        return instance
