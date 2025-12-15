from rest_framework import serializers
from .models import Test
# from .models import DiagnosticCenter
# from apps.location.models import City
# from apps.location.serializers import CitySerializer
# from apps.labfilter.models import VisitType
# from apps.labfilter.serializers import VisitTypeSerializer


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'name', 'code', 'description', 'price', 'active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        
# class DiagnosticCenterSerializer(serializers.ModelSerializer):
#     city_id = serializers.PrimaryKeyRelatedField(
#         queryset=City.objects.all(),
#         source='city',
#         write_only=True
#     )
#     tests = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Test.objects.all()
#     )
#     city = CitySerializer(read_only=True)
#     visit_type_ids = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=VisitType.objects.all(),
#         source='visit_types',
#         write_only=True
#     )
#     visit_types = VisitTypeSerializer(read_only=True, many=True)

#     class Meta:
#         model = DiagnosticCenter
#         fields = [
#             'id', 'name', 'code', 'address', 'area', 'pincode', 'contact_number', 'email',
#             'active', 'city', 'city_id', 'tests', 'visit_types', 'visit_type_ids', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['created_at', 'updated_at']
