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

    
    # ✅ Select doctor from CLIENT API
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

        # 🔹 Fetch from client API
        try:
            client_response = requests.get(client_url, timeout=10)
            client_response.raise_for_status()
            client_doctors = client_response.json()
        except Exception as e:
            return Response({"error": f"Failed to fetch from client API: {str(e)}"},
                            status=status.HTTP_502_BAD_GATEWAY)

        # 🔹 Filter logic on client data
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

        selected_doc = random.choice(filtered)

        # 🔹 Optionally save locally for testing
    #     specialization = DoctorSpeciality.objects.get(pk=specialization_id) if specialization_id else None
    #     language = Language.objects.get(pk=language_id) if language_id else None
    #     vendor = Vendor.objects.get(pk=vendor_id) if vendor_id else None

    #     doctor, created = DoctorProfessionalDetails.objects.get_or_create(
    #         name=selected_doc.get("name"),
    #         mobile_number=selected_doc.get("mobile_number"),
    #         defaults={
    #             "address": selected_doc.get("address", ""),
    #             "age": selected_doc.get("age", 0),
    #             "experience": selected_doc.get("experience", 0),
    #             "blood_group": selected_doc.get("blood_group", ""),
    #             "gender": selected_doc.get("gender",""),
    #             "image": selected_doc.get("image"),
    #             "e_consultation": selected_doc.get("e_consultation", False),
    #             "in_clinic": selected_doc.get("in_clinic", False),
    #             "specialization": specialization,
    #             "language": language,
    #             "vendor": vendor,
    #         },
    #     )

    #     serializer = self.get_serializer(doctor)
    #     return Response({
    #         "source": "client_api",
    #         "stored_locally": created,
    #         "doctor": serializer.data
    #     }, status=status.HTTP_200_OK)




    # # ✅ Filter doctors by POST body parameters
    # @action(detail=False, methods=['post'], url_path='filter')
    # def filter_doctors(self, request):
    #     e_consultation = request.data.get('e_consultation')
    #     in_clinic = request.data.get('in_clinic')
    #     specialization = request.data.get('specialization')
    #     language = request.data.get('language')
    #     vendor = request.data.get('vendor')

    #     queryset = self.queryset

    #     if e_consultation is not None:
    #         queryset = queryset.filter(e_consultation=bool(e_consultation))
    #     if in_clinic is not None:
    #         queryset = queryset.filter(in_clinic=bool(in_clinic))
    #     if specialization:
    #         queryset = queryset.filter(specialization_id=specialization)
    #     if language:
    #         queryset = queryset.filter(language_id=language)
    #     if vendor:
    #         queryset = queryset.filter(vendor_id=vendor)

    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    # # ✅ Select one doctor based on availability + specialization + language/vendor
    # @action(detail=False, methods=['post'], url_path='select')
    # def select_doctor(self, request):
    #     available_for = request.data.get('available_for')  # e_consultation or in_clinic
    #     specialization = request.data.get('specialization')
    #     language = request.data.get('language')
    #     vendor = request.data.get('vendor')

    #     if not available_for:
    #         return Response(
    #             {"error": "Missing 'available_for'. Use 'e_consultation' or 'in_clinic'."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     queryset = self.queryset

    #     if available_for == 'e_consultation':
    #         queryset = queryset.filter(e_consultation=True)
    #     elif available_for == 'in_clinic':
    #         queryset = queryset.filter(in_clinic=True)
    #     else:
    #         return Response(
    #             {"error": "Invalid value for 'available_for'. Use 'e_consultation' or 'in_clinic'."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # Optional filters
    #     if specialization:
    #         queryset = queryset.filter(specialization_id=specialization)
    #     if language:
    #         queryset = queryset.filter(language_id=language)
    #     if vendor:
    #         queryset = queryset.filter(vendor_id=vendor)

    #     if not queryset.exists():
    #         return Response(
    #             {"message": "No doctor available matching your criteria."},
    #             status=status.HTTP_404_NOT_FOUND
    #         )

    #     selected_doctor = random.choice(queryset)
    #     serializer = self.get_serializer(selected_doctor)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    
    # def perform_create(self, serializer):
    #     serializer.save(created_by=self.request.user)



class DoctorPersonalViewSet(viewsets.ModelViewSet):
    queryset = DoctorPersonalDetails.objects.all()
    serializer_class = DoctorPersonalDetailsSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,created_by=self.request.user)
        

    

class DoctorProfessionalViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfessionalDetails.objects.all()
    serializer_class = DoctorProfessionalDetailsSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related('vendor', 'specialization', 'language', 'doctor')

        # Filter by vendor_id
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        # Filter by vendor_code (e.g., ?vendor_code=APOLLO)
        vendor_code = self.request.query_params.get('vendor_code')
        if vendor_code:
            queryset = queryset.filter(vendor__code__iexact=vendor_code)

        # Filter by multiple vendor IDs (e.g., ?vendor_ids=1,2,3)
        vendor_ids = self.request.query_params.get('vendor_ids')
        if vendor_ids:
            vendor_id_list = [int(v) for v in vendor_ids.split(',') if v.isdigit()]
            queryset = queryset.filter(vendor_id__in=vendor_id_list)

        # Filter by specialization_id
        specialization_id = self.request.query_params.get('specialization_id')
        if specialization_id:
            queryset = queryset.filter(specialization_id=specialization_id)

        # Filter by language_id
        language_id = self.request.query_params.get('language_id')
        if language_id:
            queryset = queryset.filter(language_id=language_id)

        # Filter by consultation type
        e_consultation = self.request.query_params.get('e_consultation')
        if e_consultation is not None:
            queryset = queryset.filter(e_consultation=e_consultation.lower() == 'true')

        in_clinic = self.request.query_params.get('in_clinic')
        if in_clinic is not None:
            queryset = queryset.filter(in_clinic=in_clinic.lower() == 'true')

        return queryset.distinct()

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search doctors with various filters including vendor.
        Supports:
        - vendor: vendor name (partial match)
        - vendor_id: vendor ID (exact match)
        - vendor_code: vendor code like APOLLO (exact match)
        - language: language name (partial match)
        - name: doctor name (partial match)
        - specialization: specialization name (partial match)
        - e_consultation: true/false
        - in_clinic: true/false
        """
        vendor = request.query_params.get('vendor')
        vendor_id = request.query_params.get('vendor_id')
        vendor_code = request.query_params.get('vendor_code')
        language = request.query_params.get('language')
        name = request.query_params.get('name')
        specialization = request.query_params.get('specialization')
        e_consultation = request.query_params.get('e_consultation')
        in_clinic = request.query_params.get('in_clinic')

        qs = DoctorProfessionalDetails.objects.select_related('vendor', 'specialization', 'language', 'doctor')

        # Vendor filters
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        elif vendor_code:
            qs = qs.filter(vendor__code__iexact=vendor_code)
        elif vendor:
            qs = qs.filter(vendor__name__icontains=vendor)

        if language:
            qs = qs.filter(language__name__icontains=language)

        if name:
            qs = qs.filter(doctor__full_name__icontains=name)

        if specialization:
            qs = qs.filter(specialization__name__icontains=specialization)

        if e_consultation is not None:
            qs = qs.filter(e_consultation=e_consultation.lower() == 'true')

        if in_clinic is not None:
            qs = qs.filter(in_clinic=in_clinic.lower() == 'true')

        qs = qs.distinct()

        serializer = self.get_serializer(qs, many=True)
        return Response({
            "count": qs.count(),
            "results": serializer.data
        })


    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

  
