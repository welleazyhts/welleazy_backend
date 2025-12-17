from rest_framework import serializers
from apps.consultation_filter.models import DoctorSpeciality
from apps.consultation_filter.models import Language, UserLanguagePreference
from .models import City, Pincode
from apps.location.serializers import CitySerializer
from .models import Vendor



# DOCTOR SPECIALITY-----

class DoctorSpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorSpeciality
        fields=['id', 'name', 'image', 'description', 'is_active']


# LANGUAGE SELECTION-----




class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code', 'is_active']
       
      


class UserLanguagePreferenceSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)

    class Meta:
        model = UserLanguagePreference
        fields = ['id', 'user', 'language']
       


# PINCODES---



class PincodeSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source='city',
        write_only=True
    )


    class Meta:
        model = Pincode
        fields = ['id', 'code', 'city', 'city_id']
       
        





# VENDORS----


class VendorSerializer(serializers.ModelSerializer):

    specialization_name = serializers.CharField(source="specialization.name", read_only=True)
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'available', "specialization" , "specialization_name"]

       










