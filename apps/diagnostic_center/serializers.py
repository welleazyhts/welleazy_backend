from rest_framework import serializers
from apps.diagnostic_center.models import (
    DiagnosticCenter, DiagnosticCenterTest,
    DCLaboratoryCapabilities, DCContact, DCDocument
)
from apps.location.models import City
from apps.location.serializers import CitySerializer
from apps.labtest.models import Test
from apps.labtest.serializers import TestSerializer
from apps.labfilter.models import VisitType
from apps.labfilter.serializers import VisitTypeSerializer
from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage
from apps.health_packages.serializers import HealthPackageSerializer
from apps.sponsored_packages.serializers import SponsoredPackageSerializer
from apps.consultation_filter.models import Vendor


class VendorMinimalSerializer(serializers.ModelSerializer):
    """Minimal vendor info for nested serialization"""
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'code', 'logo', 'home_collection']


class DiagnosticCenterTestSerializer(serializers.ModelSerializer):
    """Serializer for DC-specific test pricing"""
    test_name = serializers.CharField(source='test.name', read_only=True)
    test_code = serializers.CharField(source='test.code', read_only=True)

    class Meta:
        model = DiagnosticCenterTest
        fields = ['id', 'test', 'test_name', 'test_code', 'price', 'discounted_price', 'is_available', 'turnaround_hours']


class DCLaboratoryCapabilitiesSerializer(serializers.ModelSerializer):
    """Serializer for DC lab capabilities"""
    class Meta:
        model = DCLaboratoryCapabilities
        fields = [
            'id',
            # Lab Sections
            'hematology', 'biochemistry', 'microbiology', 'pathology',
            'serology', 'histopathology', 'endocrinology', 'cytology', 'immunology',
            # Imaging
            'x_ray', 'digital_x_ray', 'ultra_sound', 'color_doppler', 'mammogram',
            'ct_scan', 'mri', 'pet_scan', 'nuclear_imaging',
            # Cardiac
            'ecg', 'pft', 'tmt', 'echo_2d', 'fluoroscopy',
            # Counts
            'x_ray_count', 'ct_scan_count', 'mri_count',
            # Discounts
            'x_ray_discount', 'ct_scan_discount', 'mri_discount',
        ]


class DCContactSerializer(serializers.ModelSerializer):
    """Serializer for DC contacts"""
    department_display = serializers.CharField(source='get_department_display', read_only=True)

    class Meta:
        model = DCContact
        fields = [
            'id', 'department', 'department_display', 'title', 'name',
            'designation', 'email', 'phone', 'is_primary'
        ]


class DCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for DC documents"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)

    class Meta:
        model = DCDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'file', 'file_name',
            'description', 'expiry_date', 'is_verified', 'verified_by',
            'verified_by_name', 'verified_at', 'created_at'
        ]
        read_only_fields = ['verified_by', 'verified_by_name', 'verified_at', 'created_at']


class DiagnosticCenterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_code = serializers.CharField(source='vendor.code', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = DiagnosticCenter
        fields = [
            'id', 'name', 'code', 'unique_name', 'address', 'area', 'pincode',
            'latitude', 'longitude', 'contact_number', 'email',
            'active', 'center_status', 'grade', 'provider_type',
            'home_collection', 'home_collection_charge',
            'is_nabl_accredited', 'is_cap_accredited', 'is_iso_certified',
            'vendor', 'vendor_name', 'vendor_code',
            'city', 'city_name',
            'staff_strength', 'doctor_consultants',
            'created_at', 'updated_at',
        ]


class DiagnosticCenterDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views with all fields and nested data"""
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source='city', write_only=True
    )
    vendor = VendorMinimalSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(), source='vendor',
        write_only=True, required=False, allow_null=True
    )

    # Nested related data
    lab_capabilities = DCLaboratoryCapabilitiesSerializer(read_only=True)
    contacts = DCContactSerializer(many=True, read_only=True)
    documents = DCDocumentSerializer(many=True, read_only=True)
    dc_tests = DiagnosticCenterTestSerializer(many=True, read_only=True)

    # M2M fields
    tests = TestSerializer(read_only=True, many=True)
    visit_types = VisitTypeSerializer(read_only=True, many=True)
    health_packages = HealthPackageSerializer(read_only=True, many=True)
    sponsored_packages = SponsoredPackageSerializer(read_only=True, many=True)

    # Deactivation info
    deactivated_by_name = serializers.CharField(source='deactivated_by.full_name', read_only=True)

    class Meta:
        model = DiagnosticCenter
        fields = [
            # Basic Info
            'id', 'name', 'code', 'unique_name', 'token_id',
            # Classification
            'provider_type', 'specialty_type', 'ownership', 'partnership_type',
            'center_status', 'priority', 'categorization', 'grade',
            # Corporate/Group
            'corporate_group', 'corporate_id',
            # Vendor
            'vendor', 'vendor_id', 'vendor_dc_id',
            # Location
            'address', 'area', 'pincode', 'latitude', 'longitude',
            'city', 'city_id',
            # Contact
            'std_code', 'landline_number', 'contact_number', 'alternate_number',
            'fax_number', 'email', 'website', 'contact_person',
            # Links
            'google_address', 'short_url', 'location_link', 'logo',
            # Operational
            'active', 'work_start', 'work_end', 'sunday_open',
            'slot_interval_minutes', 'slot_capacity',
            # Staff
            'staff_strength', 'doctor_consultants', 'visiting_consultants',
            'specialties_available',
            # Services
            'home_collection', 'home_collection_charge', 'home_delivery',
            'delivery_tat', 'service_area', 'service_pincodes', 'visit_type',
            'has_parking', 'health_checkup',
            # Ambulance
            'has_ambulance', 'bls_ambulance_count', 'acls_ambulance_count',
            # Accreditation
            'is_nabl_accredited', 'is_cap_accredited', 'is_iso_certified',
            'iso_type', 'recognized_by', 'accreditation_details',
            # Banking
            'bank_account_number', 'bank_account_holder', 'bank_name',
            'bank_branch', 'bank_ifsc_code', 'payment_terms',
            # Legal
            'gst_number', 'pan_number',
            # Agreement
            'mou_signed', 'mou_signed_date', 'client_assign', 'remarks',
            # Deactivation
            'deactivation_reason', 'deactivation_date', 'deactivated_by',
            'deactivated_by_name',
            # Related data
            'lab_capabilities', 'contacts', 'documents', 'dc_tests',
            'tests', 'visit_types', 'health_packages', 'sponsored_packages',
            # Timestamps
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'deactivated_by', 'deactivated_by_name']


class DiagnosticCenterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating DCs"""
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source='city', write_only=True
    )
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(), source='vendor',
        write_only=True, required=False, allow_null=True
    )

    # Lab capabilities (nested write)
    lab_capabilities = DCLaboratoryCapabilitiesSerializer(required=False)

    class Meta:
        model = DiagnosticCenter
        fields = [
            # Basic Info
            'name', 'code', 'unique_name', 'token_id',
            # Classification
            'provider_type', 'specialty_type', 'ownership', 'partnership_type',
            'center_status', 'priority', 'categorization', 'grade',
            # Corporate/Group
            'corporate_group', 'corporate_id',
            # Vendor
            'vendor_id', 'vendor_dc_id',
            # Location
            'address', 'area', 'pincode', 'latitude', 'longitude', 'city_id',
            # Contact
            'std_code', 'landline_number', 'contact_number', 'alternate_number',
            'fax_number', 'email', 'website', 'contact_person',
            # Links
            'google_address', 'short_url', 'location_link',
            # Operational
            'active', 'work_start', 'work_end', 'sunday_open',
            'slot_interval_minutes', 'slot_capacity',
            # Staff
            'staff_strength', 'doctor_consultants', 'visiting_consultants',
            'specialties_available',
            # Services
            'home_collection', 'home_collection_charge', 'home_delivery',
            'delivery_tat', 'service_area', 'service_pincodes', 'visit_type',
            'has_parking', 'health_checkup',
            # Ambulance
            'has_ambulance', 'bls_ambulance_count', 'acls_ambulance_count',
            # Accreditation
            'is_nabl_accredited', 'is_cap_accredited', 'is_iso_certified',
            'iso_type', 'recognized_by', 'accreditation_details',
            # Banking
            'bank_account_number', 'bank_account_holder', 'bank_name',
            'bank_branch', 'bank_ifsc_code', 'payment_terms',
            # Legal
            'gst_number', 'pan_number',
            # Agreement
            'mou_signed', 'mou_signed_date', 'client_assign', 'remarks',
            # Lab capabilities
            'lab_capabilities',
        ]

    def create(self, validated_data):
        lab_capabilities_data = validated_data.pop('lab_capabilities', None)
        dc = DiagnosticCenter.objects.create(**validated_data)

        if lab_capabilities_data:
            DCLaboratoryCapabilities.objects.create(
                diagnostic_center=dc, **lab_capabilities_data
            )

        return dc

    def update(self, instance, validated_data):
        lab_capabilities_data = validated_data.pop('lab_capabilities', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lab_capabilities_data:
            lab_cap, created = DCLaboratoryCapabilities.objects.get_or_create(
                diagnostic_center=instance
            )
            for attr, value in lab_capabilities_data.items():
                setattr(lab_cap, attr, value)
            lab_cap.save()

        return instance


# Backward compatibility alias
class DiagnosticCenterSerializer(DiagnosticCenterDetailSerializer):
    """Alias for backward compatibility"""
    pass