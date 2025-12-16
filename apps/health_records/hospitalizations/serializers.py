from rest_framework import serializers
from .models import HospitalizationRecord, HospitalizationDocument
from apps.dependants.serializers import DependantSerializer
from rest_framework.exceptions import ValidationError
from apps.common.serializers.dependant_mixin import DependantResolverMixin


class HospitalizationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalizationDocument
        exclude = ("created_by", "updated_by", "deleted_at")


class HospitalizationRecordSerializer(DependantResolverMixin, serializers.ModelSerializer):

    documents = HospitalizationDocumentSerializer(many=True, read_only=True)
    # dependant_data = DependantSerializer(source="dependant", read_only=True)

    hospitalization_type = serializers.SerializerMethodField()

    class Meta:
        model = HospitalizationRecord
        fields = [
            "id", "for_whom", "dependant", "dependant_data",
            "hospitalization_type", "record_name",
            "hospital_name", "admitted_date", "discharged_date",
            "doctor_name", "notes",
            "documents",
            "created_at", "updated_at",
            "created_by", "updated_by"
        ]

    def get_hospitalization_type(self, obj):
        return obj.get_hospitalization_type_display()


class HospitalizationPayloadSerializer(serializers.Serializer):
    # Serializer for creating/updating hospitalization records (without documents)

    record_id = serializers.IntegerField(required=False)

    hospitalization_type = serializers.CharField()
    record_name = serializers.CharField()
    hospital_name = serializers.CharField()

    admitted_date = serializers.DateField()
    discharged_date = serializers.DateField(required=False, allow_null=True)

    doctor_name = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    for_whom = serializers.ChoiceField(
        choices=HospitalizationRecord.FOR_WHOM_CHOICES,
        required=False,
        default="self"
    )
    dependant = serializers.IntegerField(required=False, allow_null=True)


    def validate(self, data):
        for_whom = data.get("for_whom", "self")
        dependant = data.get("dependant")

        if for_whom == "dependant" and dependant is None:
            raise ValidationError({
                "dependant": "Dependants must be provided when for_whom is 'dependant'."
            })

        if for_whom == "self":
            data["dependant"] = None

        return data
