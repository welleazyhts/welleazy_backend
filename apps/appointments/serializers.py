from rest_framework import serializers
from .models import Cart, CartItem , DoctorAvailability , ReportDocument , MedicalReports , AppointmentVoucher , Appointment
from apps.labtest.models import Test
from apps.diagnostic_center.models import DiagnosticCenter
from apps.labfilter.models import VisitType
from apps.addresses.models import Address
from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage
from apps.dependants.models import Dependant
from apps.health_packages.serializers import HealthPackageSerializer
from apps.sponsored_packages.serializers import SponsoredPackageSerializer
from apps.diagnostic_center.serializers import DiagnosticCenterSerializer
from apps.labtest.serializers import TestSerializer
from apps.dependants.serializers import DependantSerializer
from datetime import date , datetime
from apps.appointments.models import Appointment as AppointmentModel
from apps.doctor_details.models import DoctorProfessionalDetails
from apps.doctor_details.serializers import DoctorProfessionalDetailsSerializer,DoctorPersonalDetailsSerializer
# from apps.eyedental_care.models import EyeVendorAddress , DentalVendorAddress

from apps.appointments.models import CartItem
from apps.consultation_filter.models import DoctorSpeciality



class CartItemSerializer(serializers.ModelSerializer):

    # ---- WRITE FIELDS ----
    diagnostic_center_id = serializers.PrimaryKeyRelatedField(
        queryset=DiagnosticCenter.objects.all(),
        source="diagnostic_center",
        write_only=True
    )
    visit_type_id = serializers.PrimaryKeyRelatedField(
        queryset=VisitType.objects.all(),
        source="visit_type",
        required=False,
        allow_null=True,
        write_only=True
    )
    test_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Test.objects.all(),
        source="tests",
        required=False,
        allow_null=True,
        write_only=True
    )
    dependant_id = serializers.PrimaryKeyRelatedField(
        queryset=Dependant.objects.all(),
        source="dependant",
        required=False,
        allow_null=True,
        write_only=True
    )
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source="address",
        required=False,
        allow_null=True,
        write_only=True
    )
    health_package_id = serializers.PrimaryKeyRelatedField(
        queryset=HealthPackage.objects.all(),
        source="health_package",
        required=False,
        allow_null=True,
        write_only=True
    )
    sponsored_package_id = serializers.PrimaryKeyRelatedField(
        queryset=SponsoredPackage.objects.all(),
        source="sponsored_package",
        required=False,
        allow_null=True,
        write_only=True
    )




    doctor_id= serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfessionalDetails.objects.all(),
        source="doctor_details",
        required=False,
        allow_null=True,
        write_only=True
    )

    # eye_dental_appointment = AppointmentSerializer (read_only=True)
    # eye_dental_appointment_id=serializers.PrimaryKeyRelatedField(
    #     queryset=DoctorAppointment.objects.all(),
    #     source="eye_dentyal_appointment",
    #     required=False,
    #     allow_null=True,
    #     write_only=True
    # )

    # ---- READ FIELDS ----
    diagnostic_center = serializers.PrimaryKeyRelatedField(read_only=True)
    tests = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)
    health_package = serializers.PrimaryKeyRelatedField(read_only=True)
    sponsored_package = serializers.PrimaryKeyRelatedField(read_only=True)
    dependant = serializers.PrimaryKeyRelatedField(read_only=True)
    visit_type = serializers.PrimaryKeyRelatedField(read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


    class Meta:
        model = CartItem
        fields = [
            "id",
            "item_type",  # "test", "health_package",  "sponsored_package" or "doctor_appointment"
            "diagnostic_center", "diagnostic_center_id",
            "visit_type", "visit_type_id",
            "tests", "test_ids",
            "health_package", "health_package_id",
            "sponsored_package" , "sponsored_package_id",
            "doctor" , "doctor_id",
            "appointment_date","appointment_time",
            
            "for_whom", "dependant", "dependant_id",
            "address_id", "note", "price", "discount_amount", "final_price", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    # ---- VALIDATION ----
    def validate(self, data):
        dc = data.get("diagnostic_center")
        item_type = data.get("item_type", "test")

        # Test-based item validation
        if item_type == "test":
            visit_type = data.get("visit_type")
            tests = data.get("tests", [])

            if not visit_type:
                raise serializers.ValidationError("Visit type is required for test-based bookings.")

            # Check if DC supports visit type
            if not dc.visit_types.filter(id=visit_type.id).exists():
                raise serializers.ValidationError("Selected diagnostic center does not support the chosen visit type.")

            # Ensure DC offers all selected tests
            center_test_ids = set(dc.tests.values_list("id", flat=True))
            requested_ids = {t.id for t in tests}
            if not requested_ids.issubset(center_test_ids):
                raise serializers.ValidationError("One or more selected tests are not available at this diagnostic center.")

            # For home visit, ensure address provided
            if visit_type.name.lower() in ("home", "home visit") or getattr(visit_type, "code", None) == "home":
                if not data.get("address"):
                    raise serializers.ValidationError("Home visit requires an address selection.")

        # Package-based item validation
        elif item_type in ["health_package", "sponsored_package"]:
            if item_type == "health_package":
                pkg = data.get("health_package")
                if not pkg:
                    raise serializers.ValidationError("Health package is required.")
                if not dc.health_packages.filter(id=pkg.id).exists():
                    raise serializers.ValidationError("Selected health package not offered by this diagnostic center.")
            else:
                pkg = data.get("sponsored_package")
                if not pkg:
                    raise serializers.ValidationError("Sponsored package is required.")
                if not dc.sponsored_packages.filter(id=pkg.id).exists():
                    raise serializers.ValidationError("Selected sponsored package not offered by this diagnostic center.")


        elif item_type=="doctor_appointment":
            doctor_appointment=data.get("doctor_appointment") 
            if not doctor_appointment:
                raise serializers.ValidationError("Doctor Appointment is required")
            
            if hasattr(doctor_appointment, "status"):
                if getattr(doctor_appointment, "status", "").lower() !="confirmed":
                    raise serializers.ValidationError("Doctor Appointment must be confirmed before adding to cart.")
                
       
            

        else:
            raise serializers.ValidationError("Invalid item_type")
        

        # Dependant validation
        if data.get("dependant") and data.get("for_whom") == "self":
            raise serializers.ValidationError("If dependant is selected, set for_whom to 'dependant'.")

        return data

    # ---- CREATE ----
    def create(self, validated_data):
        tests = validated_data.pop("tests", [])
        cart = self.context.get("cart")

        if not cart:
            cart = Cart.objects.create(user=self.context["request"].user)

        item = CartItem.objects.create(cart=cart, **validated_data)
        if tests:
            item.tests.set(tests)
        return item


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "is_active", "created_at", "updated_at", "items", "total_amount"]

    def get_total_amount(self, obj):
        return sum([float(item.price or 0) for item in obj.items.all()])



class AddToCartSerializer(serializers.Serializer):
    diagnostic_center_id = serializers.IntegerField()
    visit_type_id = serializers.IntegerField()
    test_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    for_whom = serializers.ChoiceField(choices=CartItem.FOR_WHOM_CHOICES, default="self")
    dependant_id = serializers.IntegerField(required=False, allow_null=True)
    address_id = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)
    appointment_date = serializers.DateField()
    appointment_time = serializers.CharField()
    confirm_update = serializers.BooleanField(required=False, default=False)


    def validate(self, data):
        # fetch objects and validate
        try:
            dc = DiagnosticCenter.objects.get(id=data['diagnostic_center_id'])
        except DiagnosticCenter.DoesNotExist:
            raise serializers.ValidationError("Diagnostic center not found.")
        try:
            vt = VisitType.objects.get(id=data['visit_type_id'])
        except VisitType.DoesNotExist:
            raise serializers.ValidationError("Visit type not found.")

        if not dc.visit_types.filter(id=vt.id).exists():
            raise serializers.ValidationError("Center doesn't support chosen visit type.")

        # tests validation
        tests_qs = Test.objects.filter(id__in=data['test_ids'])
        if tests_qs.count() != len(set(data['test_ids'])):
            raise serializers.ValidationError("One or more tests not found.")
        # ensure center offers all these tests
        center_tests = set(dc.tests.values_list('id', flat=True))
        if not set(data['test_ids']).issubset(center_tests):
            raise serializers.ValidationError("Some tests not offered by this center.")

        # dependant & address checks
        if data['for_whom'] == "dependant":
            if 'dependant_id' not in data or not data['dependant_id']:
                raise serializers.ValidationError("When booking for dependant, provide dependant_id.")
            try:
                Dependant.objects.get(id=data['dependant_id'])
            except Dependant.DoesNotExist:
                raise serializers.ValidationError("Dependant not found.")
        # home visit requires address
        if vt.name.lower() in ("home", "home visit") or getattr(vt, 'code', None) == 'home':
            if 'address_id' not in data or not data['address_id']:
                raise serializers.ValidationError("Home visit requires an address.")
            try:
                Address.objects.get(id=data['address_id'])
            except Address.DoesNotExist:
                raise serializers.ValidationError("Address not found.")
        return data

class AddPackageToCartSerializer(serializers.Serializer):
    diagnostic_center_id = serializers.IntegerField()
    item_type = serializers.ChoiceField(choices=["health_package", "sponsored_package"])
    package_id = serializers.IntegerField()
    for_whom = serializers.ChoiceField(choices=CartItem.FOR_WHOM_CHOICES, default="self")
    dependant_id = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)
    appointment_date = serializers.CharField(required=True)
    appointment_time = serializers.CharField(required=True)
    confirm_update = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        try:
            dc = DiagnosticCenter.objects.get(id=data["diagnostic_center_id"])
        except DiagnosticCenter.DoesNotExist:
            raise serializers.ValidationError("Diagnostic center not found.")

        # validate package type
        if data["item_type"] == "health_package":
            try:
                pkg = HealthPackage.objects.get(id=data["package_id"])
            except HealthPackage.DoesNotExist:
                raise serializers.ValidationError("Health package not found.")
            if not dc.health_packages.filter(id=pkg.id).exists():
                raise serializers.ValidationError("This health package is not available at this diagnostic center.")
        else:
            try:
                pkg = SponsoredPackage.objects.get(id=data["package_id"])
            except SponsoredPackage.DoesNotExist:
                raise serializers.ValidationError("Sponsored package not found.")
            if not dc.sponsored_packages.filter(id=pkg.id).exists():
                raise serializers.ValidationError("This sponsored package is not available at this diagnostic center.")

        # dependant validation
        if data["for_whom"] == "dependant":
            if not data.get("dependant_id"):
                raise serializers.ValidationError("Provide dependant_id if not for self.")
            try:
                Dependant.objects.get(id=data["dependant_id"])
            except Dependant.DoesNotExist:
                raise serializers.ValidationError("Dependant not found.")

        return data
    

    
#  DOCTOR RELATED SERIALIZERS----

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.doctor.name', read_only=True)

    start_time = serializers.TimeField(
        input_formats=["%H:%M", "%H:%M:%S", "%I:%M %p"]
    )
    end_time = serializers.TimeField(
        input_formats=["%H:%M", "%H:%M:%S", "%I:%M %p"]
    )

    class Meta:
        model = DoctorAvailability
        fields = '__all__'
        read_only_fields = ["day_of_week"]

class ReportDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportDocument
        fields = ['id', 'file', 'uploaded_at']


class DoctorAppointmentToCartSerializer(serializers.Serializer):
    for_whom = serializers.ChoiceField(choices=CartItem.FOR_WHOM_CHOICES, default="self")
    dependant_id = serializers.IntegerField(required=False, allow_null=True)
    
    consultation_fee = serializers.SerializerMethodField() 
    symptoms = serializers.CharField(required=False, allow_blank=True)

    appointment_date = serializers.DateField()
  
    appointment_time = serializers.TimeField(
        input_formats=["%H:%M", "%H:%M:%S", "%I:%M %p"]
    )
   
    mode = serializers.CharField(required=False, allow_blank=True)
    
    note = serializers.CharField(required=False, allow_blank=True)

    # OUTPUT FIELDS
    doctor_details = serializers.SerializerMethodField()
    uploaded_documents = serializers.SerializerMethodField()

    def validate(self, data):
        user = self.context["request"].user

        # Doctor & specialization must be selected earlier
        doctor_id = self.context["request"].session.get("selected_doctor_id")
        specialization_id = self.context["request"].session.get("selected_specialization_id")

        if not doctor_id or not specialization_id:
            raise serializers.ValidationError("Doctor not selected.")

        try:
            doctor = DoctorProfessionalDetails.objects.get(id=doctor_id)
        except DoctorProfessionalDetails.DoesNotExist:
            raise serializers.ValidationError("Doctor not found.")

        # dependant validation
        if data["for_whom"] == "dependant":
            if not data.get("dependant_id"):
                raise serializers.ValidationError("dependant_id is required for dependant booking.")

            try:
                Dependant.objects.get(id=data["dependant_id"], user=user)
            except Dependant.DoesNotExist:
                raise serializers.ValidationError("Dependant not found.")

        # mode validation
        mode = data.get("mode")
        if doctor.in_clinic:
            data["mode"] = "in_clinic"
        elif doctor.e_consultation:
            if not mode:
                raise serializers.ValidationError("Mode is required (tele) for e-consultation.")
            if mode != "tele":
                raise serializers.ValidationError("Doctor only supports tele consultation.")
        else:
            raise serializers.ValidationError("Doctor has no available consultation mode.")

        

        return data
        
    def get_doctor_details(self,obj):
        doctor=self.context.get("doctor_obj")
        if not doctor:
            return None
        
        return{
            "id":doctor.id,
            "name":doctor.doctor.full_name,
            "specialization":doctor.specialization.name if doctor.specialization else None,
            "experience":doctor.experience_years,
            "photo":doctor.doctor.profile_photo.url if doctor.doctor.profile_photo else None,

        }
    
    def get_uploaded_documents(self,obj):
        user=self.context["request"].user

        documents=obj.documents.all().values("id","file")
        
        return[
            {
                "id":d["id"],
                
                "file":d["file"]

            }
            for d in documents
        ]

    def get_consultation_fee(self, obj):
        doctor = self.context.get("doctor_obj")
        return doctor.consultation_fee if doctor else None     
    

class AppointmentVoucherSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(source='appointment_code', read_only=True)
    doctor_speciality = serializers.CharField(source='appointment.specialization.name', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.doctor.full_name', read_only=True)
    doctor_city = serializers.CharField(source='appointment.doctor.clinic_address', read_only=True)
    consultation_type = serializers.CharField(source='appointment.mode', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient_name', read_only=True)
    disclaimer =serializers.SerializerMethodField()
    terms_conditions =serializers.SerializerMethodField()
    
    appointment_date= serializers.DateField(source='appointment.appointment_date')
    appointment_time=serializers.TimeField(source='appointment.appointment_time')

    class Meta:
        model = AppointmentVoucher
        fields = [
            'id',
            'appointment_id',
            'patient_name',
            'consultation_type',
            'doctor_name',
            'doctor_speciality',
            'doctor_city',
            'appointment_date',
            'appointment_time',
            'disclaimer',
            'terms_conditions',
            
        ]

    def get_disclaimer(self, obj):
        return "That  Confirmation will be shared in sometimes"

    def get_terms_conditions(self, obj):
        return(
             "Service Scope: Welleazy Healthtech Solutions offers tele/video consultations...",
             "Informed Consent: By initiating a teleconsultation...",
             "Clinical Limitations: Teleconsultation does not replace an in-person medical examination...",
             "Privacy & Data Protection: All virtual interactions are encrypted...",
             "Emergency Exclusion: These services are not intended for life-threatening scenarios...",
             "Availability & Connectivity: Consultations are subject to clinician availability..."
        )  
    

class MedicalReportSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MedicalReports
        fields = ["id", "url"]

    def get_url(self, obj):
        return obj.file.url if obj.file else None
    



# EYE & DENTAL APPOINTMENTS----


# class EyeAppointmentToCartSerializer(serializers.Serializer):
#     eye_vendor_centers_id = serializers.IntegerField()
#     dependant_name=serializers.CharField(source='dependant.name',read_only=True)
#     appointment_date = serializers.DateField()
#     appointment_time = serializers.TimeField()
#     consultation_fee = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

#     for_whom = serializers.ChoiceField(choices=CartItem.FOR_WHOM_CHOICES, default="self")
#     dependant_id = serializers.IntegerField(required=False, allow_null=True)

#     note = serializers.CharField(required=False, allow_blank=True)

#     def validate(self, data):
#         user = self.context["request"].user

#         # Vendor center validation
#         center_id = data["eye_vendor_centers_id"]
#         try:
#             vendor_center = EyeVendorAddress.objects.get(id=center_id)
#         except EyeVendorAddress.DoesNotExist:
#             raise serializers.ValidationError("Invalid eye vendor center.")

#         data["vendor_center"] = vendor_center
#         data["vendor"] = vendor_center.vendor

#         # dependant validation
#         if data["for_whom"] == "dependant":
#             if not data.get("dependant_id"):
#                 raise serializers.ValidationError("dependant_id is required for dependant booking.")
#             try:
#                 Dependant.objects.get(id=data["dependant_id"], user=user)
#             except Dependant.DoesNotExist:
#                 raise serializers.ValidationError("Dependant not found.")

#         return data
    
#     def get_consultation_fee(self, obj):
#         doctor = self.context.get("doctor_obj")
#         return doctor.consultation_fee if doctor else None     
    
    

#     class Meta:
#         model = Appointment
#         fields = [
#             "patient_name",
#             "dependant_name",
#             "vendor_name",
#             "status",
#             "for_whom",
#             "dependant_id",
#             "appointment_date",
#             "appointment_time",
#             "consultation_fee",
#             "note",
#             "eye_vendor_centers_id",
#         ]
        
#         extra_kwargs = {
#             "patient_name": {"required": True},
#             "appointment_date": {"required": True},
#             "appointment_time": {"required": True},
#         }
    
    # def create(self, validated_data):
    #     # Extract the vendor center ID (not a model field)
    #     center_id = validated_data.pop("eye_vendor_centers_id")

    #     # External lookup
    #     eye_vendor_center = EyeVendorAddress.objects.get(id=center_id)

    #     # Create appointment with correct fields
    #     appointment = Appointment.objects.create(
    #         vendor=eye_vendor_center.vendor,
    #         eye_vendor_centers=eye_vendor_center,
    #         Service_type="eye",
    #         **validated_data
    #     )
#             "appointment_time": {"required": True},
#         }


    # def create(self, validated_data):
    #     # Extract the vendor center ID (not a model field)
    #     center_id = validated_data.pop("dental_vendor_centers_id")

    #     # External lookup
    #     dental_vendor_center = DentalVendorAddress.objects.get(id=center_id)

    #     # Create appointment with correct fields
    #     appointment = Appointment.objects.create(
    #         vendor=dental_vendor_center.vendor,
    #         dental_vendor_centers=dental_vendor_center,
    #         Service_type="dental",
    #         **validated_data
    #     )

    #     return appointment