from rest_framework import serializers
from .models import PharmacyVendor, PharmacyCategory, PharmacyBanner, Medicine , MedicineDetails , MedicineCoupon ,PharmacyOrderItem , PharmacyOrder

class PharmacyVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyVendor
        fields = "__all__"
        read_only_fields = ["created_by", "updated_by", "created_at", "updated_at", "deleted_at"]


class PharmacyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyCategory
        fields = "__all__"
        read_only_fields = ["created_by", "updated_by", "created_at", "updated_at", "deleted_at"]


class PharmacyBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyBanner
        fields = "__all__"
        read_only_fields = ["created_by", "updated_by", "created_at", "updated_at", "deleted_at"]

class MedicinesDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineDetails
        fields = "__all__"
        read_only_fields = ["medicine"]



class MedicineSerializer(serializers.ModelSerializer):
    details=MedicinesDetailsSerializer( read_only=True)
    # WRITE FIELDS (input)
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=PharmacyVendor.objects.all(),
        required=False,
        allow_null=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=PharmacyCategory.objects.all(),
        required=False,
        allow_null=True
    )

    # READ FIELDS (output)
    vendor_id = serializers.IntegerField(source="vendor.id", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)

    category_id = serializers.IntegerField(source="category.id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Medicine
        fields = "__all__"
        read_only_fields = ["created_by", "updated_by", "created_at", "updated_at", "deleted_at"]




class MedicineCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineCoupon
        fields = "__all__"


class PharmacyOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source="medicine.name", read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = PharmacyOrderItem
        fields = ["medicine_name", "quantity", "amount", "total_amount"]

    def get_total_amount(self, obj):
        return float(obj.total_amount)


class PharmacyOrderSerializer(serializers.ModelSerializer):
    items = PharmacyOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = PharmacyOrder
        fields = [
            "order_id",
            "status",
            "patient_name",
            "ordered_date",
            "ordered_time",
            "address",
            "invoice",
            "items",
        ]
