"""
Customer-facing Case Serializers
Serializers for customers to view and manage their cases.
"""
from rest_framework import serializers
from .models import (
    Case, CaseItem, CaseRemark, CaseDocument, CaseStatusLog
)


class CaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseItem
        fields = [
            'id', 'item_type', 'item_name',
            'quantity', 'unit_price', 'discount', 'final_price', 'status'
        ]
        read_only_fields = ['final_price']


class CaseRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseRemark
        fields = ['id', 'remark_type', 'remark', 'created_at']
        read_only_fields = ['created_at']


class CaseRemarkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseRemark
        fields = ['remark_type', 'remark']


class CaseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDocument
        fields = [
            'id', 'document_type', 'file', 'file_name',
            'description', 'created_at'
        ]


class CaseStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStatusLog
        fields = ['id', 'from_status', 'to_status', 'reason', 'created_at']


class CaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    dc_name = serializers.CharField(source='diagnostic_center.name', read_only=True)

    class Meta:
        model = Case
        fields = [
            'id', 'case_id', 'patient_name',
            'service_type', 'status', 'source',
            'vendor_name', 'dc_name',
            'scheduled_date', 'scheduled_time',
            'final_amount', 'payment_status',
            'created_at'
        ]


class CaseDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views"""
    items = CaseItemSerializer(many=True, read_only=True)
    documents = CaseDocumentSerializer(many=True, read_only=True)

    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    diagnostic_center_name = serializers.CharField(source='diagnostic_center.name', read_only=True)

    class Meta:
        model = Case
        fields = [
            'id', 'case_id',
            # Patient
            'patient_name', 'patient_phone', 'patient_email',
            # Service
            'service_type',
            'vendor', 'vendor_name', 'vendor_booking_id',
            'diagnostic_center', 'diagnostic_center_name',
            # Status
            'status', 'source',
            'visit_type', 'payment_type',
            # Scheduling
            'scheduled_date', 'scheduled_time', 'completed_at',
            'address_text',
            # Financial
            'total_amount', 'discount_amount', 'final_amount',
            'payment_status',
            # Notes
            'notes',
            # Timestamps
            'created_at', 'updated_at',
            # Nested
            'items', 'documents'
        ]
        read_only_fields = ['case_id', 'created_at', 'updated_at', 'final_amount', 'status']


class CaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cases"""
    items = CaseItemSerializer(many=True, required=False)

    class Meta:
        model = Case
        fields = [
            # Patient
            'patient_name', 'patient_phone', 'patient_email',
            'is_dependant', 'dependant',
            # Service
            'service_type', 'vendor', 'diagnostic_center',
            # Scheduling
            'scheduled_date', 'scheduled_time',
            'address', 'address_text',
            'visit_type',
            # Notes
            'notes',
            # Items
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        case = Case.objects.create(**validated_data)

        for item_data in items_data:
            CaseItem.objects.create(case=case, **item_data)

        return case
