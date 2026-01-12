from django.shortcuts import render

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DoctorSpeciality
from .serializers import DoctorSpecialitySerializer
from django.conf import settings
import requests
# from django.contrib.auth.models import User
from django.conf import settings
from apps.consultation_filter.models import Language, UserLanguagePreference
from apps.consultation_filter.serializers import LanguageSerializer, UserLanguagePreferenceSerializer
from .models import City,Pincode
from .serializers import CitySerializer, PincodeSerializer


from apps.location.views import CityViewSet
from .models import Vendor
from .serializers import VendorSerializer
import random
# from django_filters.rest_framework import DjangoFilterBackend





 # DOCTOR SPECIALITY

class DoctorSpecializationViewSet(viewsets.ModelViewSet):
    
    permission_classes=[IsAuthenticated]
    queryset = DoctorSpeciality.objects.filter(deleted_at__isnull=True)
    serializer_class = DoctorSpecialitySerializer

    def list(self, request):
        # Return list of tests (from external API or local DB).
        client_api_url = getattr(settings, "CLIENT_DOCTORSPECIALITY_API_URL", None)

        # Optional: Fetch from Client API
        if client_api_url:
            try:
                headers = {}
                client_api_token = getattr(settings, "CLIENT_API_TOKEN", None)
                if client_api_token:
                    headers["Authorization"] = f"Bearer {client_api_token}"

                response = requests.get(client_api_url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                formatted_data = [
                    {
                        "id": item.get("id"),
                        "name": item.get("doctorspeciality_name") or item.get("name"),
                        "description": item.get("description"),
                        
                    }
                    for item in data
                ]
                return Response(formatted_data, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch client API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )


           # -- local DB
        queryset = self.get_queryset().order_by("name")
        serializer = DoctorSpecialitySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        # Custom create with duplicate check and created_by tracking
        name = request.data.get('name')
        description=request.data.get('description')
        image=request.data.get('image')
        is_active = request.data.get('is_active', True)

        if DoctorSpeciality.objects.filter(name__iexact=name).exists():
            return Response({"message": "Specialization already exists"}, status=status.HTTP_400_BAD_REQUEST)

        specialization = DoctorSpeciality.objects.create(
            name=name,
            description=description,
            image=image,
            is_active=is_active,
            created_by=request.user if request.user.is_authenticated else None
        )
        serializer = self.get_serializer(specialization)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def active(self, request):
        qs = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],url_path='search/(?P<name>[^/.]+)')
    def search(self, request,name=None):
        qs = DoctorSpeciality.objects.filter(name__icontains=name)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


    # LANGUAGE SELECTION


class LanguageViewSet(viewsets.ModelViewSet):
  
    permission_classes=[IsAuthenticated]
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    lookup_field = 'name'
    

    def list(self, request):
        client_api_url = getattr(settings, "CLIENT_LANGUAGE_API_URL", None)

        # Optional: Fetch from Client API
        if client_api_url:
            try:
                headers = {}
                client_api_token = getattr(settings, "CLIENT_API_TOKEN", None)
                if client_api_token:
                    headers["Authorization"] = f"Bearer {client_api_token}"

                response = requests.get(client_api_url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                formatted_data = [
                    {
                        "id": item.get("id"),
                        "name": item.get("language_name") or item.get("name"),
                        "code": item.get("code"),
                        
                    }
                    for item in data
                ]
                return Response(formatted_data, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch client API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

  
      # LOCAL DB
       
        languages = self.get_queryset()
        serializer = self.get_serializer(languages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def select(self, request):
        
        created_by=request.user if request.user.is_authenticated else None
        lang_code = request.data.get("language_code")
        if not lang_code:
            return Response({"error": "language_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            language = Language.objects.get(code__iexact=lang_code)
        except Language.DoesNotExist:
            return Response({"error": "Language not found"}, status=status.HTTP_404_NOT_FOUND)

        # Assuming user is authenticated
        user = request.user
        created_by=request.user if request.user.is_authenticated else None
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        preference,created = UserLanguagePreference.objects.get_or_create(user=user)
        preference.language = language
        preference.save()

        serializer = UserLanguagePreferenceSerializer(preference)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


    # PINCODES




class PincodeViewSet(viewsets.ModelViewSet):
   
    permission_classes=[IsAuthenticated]
    queryset = Pincode.objects.select_related('city').all()
    serializer_class = PincodeSerializer
    lookup_field='id'

    def list(self, request):
        client_api_url = getattr(settings, "CLIENT_PINCODE_API_URL", None)

        # Optional: Fetch from Client API
        if client_api_url:
            try:
                headers = {}
                client_api_token = getattr(settings, "CLIENT_API_TOKEN", None)
                if client_api_token:
                    headers["Authorization"] = f"Bearer {client_api_token}"

                response = requests.get(client_api_url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                formatted_data = [
                    {
                        "id": item.get("id"),
                        "code": item.get("pincode") or item.get("code"),
                        "city":{
                            "id":item.get("city_id"),
                            "name":item.get("city_name")
                        }
                        
                    }
                    for item in data
                ]
                return Response(formatted_data, status=status.HTTP_200_OK)

            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch client API: {e}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
    
    # LOCAL DB
        queryset = Pincode.objects.select_related("city").all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'] , url_path='search/(?P<code>[^/.]+)')
    def search(self, request, code=None):
        
        if not code:
            return Response({"error": "Pincode is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pincode = Pincode.objects.select_related("city").get(code=code)
            serializer = self.get_serializer(pincode)
            serializer.save(created_by=self.request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Pincode.DoesNotExist:
            return Response({"error": "Pincode not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='city/(?P<city_id>[^/.]+)')
    def by_city(self, request, city_id=None):
       
        try:
            city = City.objects.get(id=city_id)
        except City.DoesNotExist:
            return Response({"error": "City not found"}, status=status.HTTP_404_NOT_FOUND)

        pincodes = Pincode.objects.filter(city=city)
        serializer = self.get_serializer(pincodes, many=True)
        return Response({
            "city": city.name,
            "pincodes": serializer.data
        }, status=status.HTTP_200_OK)
    



 # VENDOR LIST


class VendorViewSet(viewsets.ModelViewSet):
   
    permission_classes=[IsAuthenticated]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    # filter_backends =[DjangoFilterBackend]
    # filterset_fields = ['name']

    # 🔹 Helper function to sync data from client API
    def _sync_vendors_from_client(self):
        client_url = getattr(settings, "CLIENT_VENDOR_URL", None)
        if not client_url:
            raise ValueError("CLIENT_VENDOR_URL not set in settings.py")

        try:
            response = requests.get(client_url, timeout=10)
            response.raise_for_status()
            client_vendors = response.json()
        except requests.RequestException as e:
            raise ValueError(f"Error fetching client vendor list: {e}")

        for data in client_vendors:
            # Map specialization
            spec_name = data.get("specialization")
            specialization = None
            if spec_name:
                specialization, _ = DoctorSpeciality.objects.get_or_create(name=spec_name)

            Vendor.objects.update_or_create(
                external_id=data.get("id"),
                defaults={
                    "name": data.get("name", "").strip(),
                    "available": data.get("available", True),
                    "specialization": specialization,     # ← IMPORTANT FIX
                },
            )



    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset
    

    
    @action(detail=False, methods=['get'], url_path='list')
    def list_vendors(self, request):
        # Fetch vendors from client API, sync to DB, and list all vendor names.
        # GET /api/vendors/list/
        try:
            self._sync_vendors_from_client()
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        vendors = Vendor.objects.all().order_by("name")
        vendor_names = vendors.values_list("name", flat=True)
        return Response({"vendors": list(vendor_names)}, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


    @action(detail=False, methods=['post'], url_path='select')
    def select_vendor(self, request):
        
        name = request.data.get("name")
        specialization_name=request.data.get("specialization")
        if not name:
            return Response({"error": "Vendor name is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not specialization_name:
            return Response({"error": "Specialization name is required."} , status=400)
        
        
        # Sync data before selecting
        # try:
        #     self._sync_vendors_from_client()
        # except ValueError as e:
        #     return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        try:
            specialization= DoctorSpeciality.objects.get(name__iexact=specialization_name)
        except DoctorSpeciality.DoesNotExist:
            return Response({"error": "Specialization not found."} , status=404)
        
        try:
            vendor = Vendor.objects.get(name__iexact=name)
        except Vendor.DoesNotExist:
            return Response({"message": f"Vendor '{name}' not found."}, status=status.HTTP_404_NOT_FOUND)

        if not vendor.available:
            return Response({"message": f"Vendor '{vendor.name}' is not currently available."}, status=status.HTTP_200_OK)

        serializer = self.get_serializer(vendor)
        return Response(serializer.data, status=status.HTTP_200_OK)



