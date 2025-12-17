from rest_framework import serializers
from .models import GymCenter, GymPackage, Voucher, Dependant
from django.contrib.auth import get_user_model
from apps.dependants.models import Dependant

User = get_user_model()

class GymCenterSerializer(serializers.ModelSerializer):
    logo=serializers.ImageField(use_url=True)

    class Meta:
        model = GymCenter
        fields = ['id', 'name', 'type', 'business_line', 'address', 'city', 'state', 'logo']


class GymPackageSerializer(serializers.ModelSerializer):
    vendor_logo=serializers.ImageField(use_url=True)

    class Meta:
        model = GymPackage
        fields = ['id', 'title', 'duration_months', 'original_price', 'discounted_price', 'discount_percent', 'features', 'vendor_logo']


class DependantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependant
        fields = ['id', 'name', 'relationship', 'dob']


#  NO DISPLAY CONTENTS-----
class VoucherCreateSerializer(serializers.ModelSerializer):
    booking_for = serializers.ChoiceField(choices=[('self', 'Self'), ('dependant','Dependant')])
    
    dependant_id = serializers.IntegerField(required=False, write_only=True)
    dependant = DependantSerializer(required=False)
    package_id = serializers.IntegerField(write_only=True)
    gym_center_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Voucher
        fields = [
            "booking_for",
            "dependant",
            "dependant_id",
            "package_id",
            "gym_center_id",
            "contact_number",
            "email",
            "city",
            "state",
            "address",
            "amount_paid",
            "currency",
        ]

    def validate(self, data):
        if data["booking_for"] == "dependant" and not (data.get("dependant_id") or data.get("dependant")):
            raise serializers.ValidationError("Dependants must be provided when booking_for='dependant'")
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        package_id = validated_data.get("package_id")
        gym_center_id = validated_data.get("gym_center_id")

        if not package_id:
            raise serializers.ValidationError({"package_id": "This field is required."})
        if not gym_center_id:
            raise serializers.ValidationError({"gym_center_id": "This field is required."})

        package = GymPackage.objects.get(id=package_id)
        gym_center = GymCenter.objects.get(id=gym_center_id)

        dependant = None
        if validated_data.get('dependant_id'):
            dependant = Dependant.objects.get(id=validated_data["dependant_id"])
        elif validated_data.get("dependant"):
            dep_ser = DependantSerializer(data=validated_data["dependant"])
            dep_ser.is_valid(raise_exception=True)
            dependant = dep_ser.save(user=user)

        voucher = Voucher.objects.create(
            user=user,
            package=package,
            gym_center=gym_center,
            booking_for=validated_data["booking_for"],
            dependant=dependant,
            contact_number=validated_data.get("contact_number"),
            email=validated_data.get("email"),
            city=validated_data.get("city"),
            state=validated_data.get("state") , 
            address=validated_data.get("address"),
            amount_paid=validated_data.get("amount_paid", package.discounted_price),
            currency=validated_data.get("currency", "INR"),
            status="pending"
        )
        return voucher


# ONLY DISPLAY CONTENTS------
class VoucherDetailSerializer(serializers.ModelSerializer):
    voucher_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    selected_package = serializers.SerializerMethodField()
    
    gym_center_name = serializers.CharField(source="gym_center.name", read_only=True)
    voucher_datetime = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = [
            "voucher_id",
            "name",
            "selected_package",
            
            "gym_center_name",
            "voucher_datetime",
        ]

    def get_voucher_id(self, obj):
        return f"#{obj.pk}"

    def get_name(self, obj):
        if obj.booking_for == "dependant" and obj.dependant:
            return obj.dependant.name
        return  obj.user.name

    def get_selected_package(self, obj):
        return f"{obj.package.duration_months} (Months)"

 
    def get_voucher_datetime(self, obj):
        return obj.created_at.strftime("%m/%d/%Y %I:%M:%S %p")
