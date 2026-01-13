from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets,status
from .models import DoctorProfessionalDetails, DoctorPersonalDetails
from .serializers import DoctorProfessionalDetailsSerializer,DoctorPersonalDetailsSerializer
from rest_framework.permissions import IsAuthenticated
import random,requests
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response


from rest_framework.exceptions import ValidationError



class DoctorViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAuthenticated]
    queryset = DoctorProfessionalDetails.objects.all()
    serializer_class = DoctorProfessionalDetailsSerializer

    
    # Select doctor from CLIENT API
    @action(detail=False, methods=['post'], url_path='select-from-client')
    def select_from_client(self, request):
        available_for = request.data.get('available_for')
        specialization_id = request.data.get('specialization')
        language_id = request.data.get('language')
        vendor_id = request.data.get('vendor')

        client_url = getattr(settings, "CLIENT_DOCTOR_URL", None)
        if not client_url:
            return Response({"error": "CLIENT_DOCTOR_URL not configured in settings.py"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Fetch from client API
        try:
            client_response = requests.get(client_url, timeout=10)
            client_response.raise_for_status()
            client_doctors = client_response.json()
        except Exception as e:
            return Response({"error": f"Failed to fetch from client API: {str(e)}"},
                            status=status.HTTP_502_BAD_GATEWAY)

        # Filter logic on client data
        filtered = []
        for doc in client_doctors:
            if available_for == "e_consultation" and not doc.get("e_consultation"):
                continue
            if available_for == "in_clinic" and not doc.get("in_clinic"):
                continue
            if specialization_id and str(doc.get("specialization")) != str(specialization_id):
                continue
            if language_id and str(doc.get("language")) != str(language_id):
                continue
            if vendor_id and str(doc.get("vendor")) != str(vendor_id):
                continue
            filtered.append(doc)

        if not filtered:
            return Response({"message": "No doctors available from client API."},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(filtered, status=status.HTTP_200_OK)



class DoctorPersonalViewSet(viewsets.ModelViewSet):
    queryset = DoctorPersonalDetails.objects.all()
    serializer_class = DoctorPersonalDetailsSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,created_by=self.request.user)
        

    

class DoctorProfessionalViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfessionalDetails.objects.all()
    serializer_class = DoctorProfessionalDetailsSerializer

    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
       

        vendor = request.query_params.get('vendor')
        language = request.query_params.get('language')
        name = request.query_params.get('name')
        specialization = request.query_params.get('specialization')

        qs = DoctorProfessionalDetails.objects.all()

        # Apply filters only if provided
        if vendor:
            qs = qs.filter(vendor__name__icontains=vendor)

        if language:
            qs = qs.filter(language__name__icontains=language)

        if name:
            qs = qs.filter(doctor__full_name__icontains=name)

        if specialization:
            qs = qs.filter(specialization__name__icontains=specialization)

        qs = qs.distinct()

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

  
