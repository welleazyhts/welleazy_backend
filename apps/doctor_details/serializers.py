from rest_framework import serializers
from .models import DoctorPersonalDetails,DoctorProfessionalDetails
from apps.consultation_filter.serializers import VendorSerializer, LanguageSerializer , DoctorSpecialitySerializer
from apps.consultation_filter.models import Vendor,Language,DoctorSpeciality
from apps.location.models import City

class DoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all()
    )
   

    class Meta:
        model = DoctorPersonalDetails
        fields = [
            "id", "full_name", "gender", "dob","age","blood_group",
            "phone", "email", "address", "profile_photo", "city",
        ]




class DoctorProfessionalDetailsSerializer(serializers.ModelSerializer):

    # Read only
    specialization = DoctorSpecialitySerializer( many=True ,read_only=True)
    vendor = VendorSerializer(read_only=True)
    language = LanguageSerializer(many=True ,read_only=True)
    name = serializers.CharField(source="doctor.full_name", read_only=True)
    city_name= serializers.CharField( source="doctor.city.name" , read_only = True)

    # Write only
    specialization_id = serializers.PrimaryKeyRelatedField(
        queryset=DoctorSpeciality.objects.all(),
        source="specialization",
        many=True,
        write_only=True
    )
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source="vendor",
        write_only=True
    )
    language_id = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(),
        source="language",
        many=True,
        write_only=True
    )

    class Meta:
        model = DoctorProfessionalDetails
        fields = [
            "id",
            "doctor",
            "name",
            "vendor", "vendor_id",
            "specialization", "specialization_id",
            "language", "language_id",
            "city_name",
            "experience_years",
            "consultation_fee",
            "license_number",
            "clinic_address",
            "e_consultation",
            "in_clinic",
        ]