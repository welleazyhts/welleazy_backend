from rest_framework import serializers
from .models import EyeTreatment, DentalTreatment , EyeDentalCareBooking
from apps.dependants.models import Dependant




class EyeTreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EyeTreatment
        fields = "__all__"


class DentalTreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DentalTreatment
        fields = "__all__"




   

   
    # def create(self, validated_data):
    #     request = self.context["request"]
    #     user = request.user

    #     dependant_name = None
    #     dependant_relationship = None

    #     if validated_data.get("booking_for") == "dependant":
    #         dep_id = validated_data.pop("dependant_id")
    #         dependant_obj = Dependant.objects.get(id=dep_id, user=user)
    #         dependant_name = dependant_obj.name
    #         dependant_relationship = dependant_obj.relationship

    #     voucher = EyeDentalVoucher.objects.create(
    #         user=user,
    #         booking_for=validated_data.get("booking_for"),

    #         dependant_name=dependant_name,
    #         dependant_relationship=dependant_relationship,

    #         service_type=validated_data.get("service_type"),

    #         eye_treatment=validated_data.get("eye_treatment"),
    #         dental_treatment=validated_data.get("dental_treatment"),

    #         eye_vendor=validated_data.get("eye_vendor"),
    #         dental_vendor=validated_data.get("dental_vendor"),

    #         name=validated_data.get("name"),
    #         contact_number=validated_data.get("contact_number"),
    #         email=validated_data.get("email"),
    #         state=validated_data.get("state"),
    #         city=validated_data.get("city"),
    #         address=validated_data.get("address"),
    # )

    #     return voucher


# class EyeDentalVoucherSerializer(serializers.ModelSerializer):

#     request_id = serializers.CharField(read_only=True)
#     service_name = serializers.SerializerMethodField()
#     treatment_name = serializers.SerializerMethodField()
#     vendor_name = serializers.SerializerMethodField()
#     center_address = serializers.SerializerMethodField()
#     name = serializers.SerializerMethodField()  # self or dependant

#     class Meta:
#         model = EyeDentalVoucher
#         fields = [
#             "request_id",
#             "name",
#             "vendor_name",
#             "center_address",
#             "service_name",
#             "treatment_name",
#             "created_at",
           
#         ]

#     def get_name(self, obj):
#         if obj.booking_for == "dependant":
#             return obj.dependant_name
#         user=obj.user
#         return user.name
    
     

#     def get_vendor_name(self, obj):
#         if obj.service_type == "eye" and obj.eye_vendor:
#             return obj.eye_vendor.vendor.name
#         if obj.service_type == "dental" and obj.dental_vendor:
#             return obj.dental_vendor.vendor.name
#         return None

#     def get_center_address(self, obj):
#         if obj.service_type == "eye" and obj.eye_vendor:
#             return obj.eye_vendor.address
#         if obj.service_type == "dental" and obj.dental_vendor:
#             return obj.dental_vendor.address
#         return None

#     def get_service_name(self, obj):
#         return "Eye Care" if obj.service_type == "eye" else "Dental Care"

#     def get_treatment_name(self, obj):
#         if obj.service_type == "eye" and obj.eye_treatment:
#             return obj.eye_treatment.name
#         if obj.service_type == "dental" and obj.dental_treatment:
#             return obj.dental_treatment.name
#         return None







class EyeDentalCareBookingSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    address_type_name = serializers.CharField(
        source="address.address_type.name",
        read_only=True,
    )

    eye_treatment_name = serializers.CharField(
        source="eye_treatment.name",
        read_only=True,
    )
    dental_treatment_name = serializers.CharField(
        source="dental_treatment.name",
        read_only=True,
    )

    class Meta:
        model = EyeDentalCareBooking
        fields = "__all__"
        read_only_fields = (
            "user",
            "name",
            "email",
            "contact_number",
            "state",
            "city",
            "address_text",
            "address",
            "status",
            "created_at",
            "updated_at",
        )

class EyeDentalCareBookingFinalSerializer(serializers.Serializer):
    for_whom = serializers.ChoiceField(choices=["self", "dependant"])
    requirements = serializers.CharField(required=False, allow_blank=True)

    dependant = serializers.IntegerField(required=False, allow_null=True)

    address = serializers.IntegerField(required=False, allow_null=True)
    state = serializers.IntegerField(required=False, allow_null=True)
    city = serializers.IntegerField(required=False, allow_null=True)
    address_text = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["for_whom"] == "dependant" and not data.get("dependant"):
            raise serializers.ValidationError(
                {"dependant": "Dependant is required when for_whom='dependant'."}
            )

        if data["for_whom"] == "self":
            data["dependant"] = None

        has_saved_address = bool(data.get("address"))
        has_manual_text = bool(data.get("state") and data.get("city") and data.get("address_text"))

        if not has_saved_address and not has_manual_text:
            raise serializers.ValidationError({
                "address": "Select a saved address or enter address_text."
            })

        if has_saved_address and has_manual_text:
            raise serializers.ValidationError({
                "address": "Choose either saved address OR address_text, not both."
            })

        return data
