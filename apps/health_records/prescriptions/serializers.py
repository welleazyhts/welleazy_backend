from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from .models import PrescriptionRecord, PrescriptionParameter, PrescriptionDocument
from apps.consultation_filter.serializers import DoctorSpecialitySerializer
from apps.dependants.serializers import DependantSerializer
from apps.common.serializers.dependant_mixin import DependantResolverMixin


class PrescriptionParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionParameter
        exclude = ("created_by", "updated_by", "deleted_at")
        read_only_fields = ("id", "record")


class PrescriptionDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionDocument
        exclude = ("created_by", "updated_by", "deleted_at")
        read_only_fields = ("id", "record")


class PrescriptionRecordSerializer(DependantResolverMixin, serializers.ModelSerializer):
    parameters = PrescriptionParameterSerializer(many=True, read_only=True)
    documents = PrescriptionDocumentSerializer(many=True, read_only=True)
    
    specialization_data = DoctorSpecialitySerializer(
        source="doctor_specialization",
        read_only=True
    )
    
    record_type = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionRecord
        fields = [
            "id", "for_whom", "dependant", "dependant_data",
            "record_type", "record_name",
            "doctor_name", "doctor_specialization", "specialization_data",
            "record_date", "reason",
            "parameters", "documents",
            "created_at", "updated_at",
            "created_by", "updated_by"
        ]
        read_only_fields = ("created_at", "updated_at", "created_by", "updated_by")
        
    def get_record_type(self, obj):
        return obj.get_record_type_display()


class ParameterInputSerializer(serializers.Serializer):
    parameter_name = serializers.CharField(required=True)
    result = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)
    start_range = serializers.CharField(required=False, allow_blank=True)
    end_range = serializers.CharField(required=False, allow_blank=True)


class RecordPayloadSerializer(serializers.Serializer):
    # Serializer for creating/updating prescription records with optional parameters
    record_id = serializers.IntegerField(required=False)
    record_date = serializers.DateField()
    record_type = serializers.CharField()
    record_name = serializers.CharField()
    doctor_name = serializers.CharField()
    doctor_specialization = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)
    for_whom = serializers.ChoiceField(
        choices=PrescriptionRecord.FOR_WHOM_CHOICES,
        required=False,
        default="self"
    )
    dependant = serializers.IntegerField(required=False, allow_null=True)
    
    # Optional: parameters can be provided during create/update
    parameters = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )
    
    keep_parameters = serializers.ListField(child=serializers.IntegerField(), required=False)
    keep_documents = serializers.ListField(child=serializers.IntegerField(), required=False)
    
    def validate(self, data):
        for_whom = data.get("for_whom", "self")
        dependant = data.get("dependant")

        if for_whom == "dependant" and dependant is None:
            raise ValidationError({
                "dependant": "Dependant must be provided when for_whom is 'dependant'."
            })

        if for_whom == "self":
            data["dependant"] = None

        return data