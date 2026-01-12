from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    InsurancePolicyRecord,
    InsuranceFloaterMember,
    InsurancePolicyDocument,
)

from apps.dependants.models import Dependant
from apps.dependants.serializers import DependantSerializer
from apps.common.serializers.dependant_mixin import DependantResolverMixin


# basic serializers (for nested output)

class InsurancePolicyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicyDocument
        exclude = ("created_by", "updated_by", "deleted_at")


class InsuranceFloaterMemberSerializer(serializers.ModelSerializer):
    dependant_data = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceFloaterMember
        exclude = ("created_by", "updated_by", "deleted_at")
        
    def get_dependant_data(self, obj):
        if obj.is_self:
            user = obj.policy.user
            return None

        if obj.dependant:
            return DependantSerializer(obj.dependant).data

        return None

    def get_patient_name(self, obj):
        if obj.is_self:
            user = obj.policy.user
            return getattr(user, "name", user.name) or user.username
        
        if obj.dependant:
            return obj.dependant.name
            
        return "Unknown"


class InsurancePolicyRecordSerializer(DependantResolverMixin,
                                      serializers.ModelSerializer):

    dependant_data = serializers.SerializerMethodField()
    floater_members = InsuranceFloaterMemberSerializer(
        many=True, read_only=True
    )
    documents = InsurancePolicyDocumentSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = InsurancePolicyRecord
        fields = [
            "id",
            "policy_owner_type",
            "plan_type",

            # "for_whom",
            "dependant",
            "dependant_data",
            "patient_name",

            "is_self_included",

            # "policy_holder_name",
            "policy_from",
            "policy_to",
            "type_of_insurance",
            "insurance_company",
            "policy_number",
            "policy_name",
            "sum_assured",
            "premium_amount",
            "tpa",
            "nominee",

            "renewal_reminder_enabled",
            "renewal_frequency",
            "renewal_reminder_type",
            "renewal_reminder_value",

            "group_policy_details",
            "policy_features",
            "notes",

            "floater_members",
            "documents",

            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ("created_at", "updated_at", "created_by", "updated_by")




# input payload serializers


class FloaterMemberInputSerializer(serializers.Serializer):
    dependant_id = serializers.IntegerField(required=False, allow_null=True)
    uhid = serializers.CharField(required=False, allow_blank=True)


class InsurancePolicyPayloadSerializer(serializers.Serializer):

    policy_owner_type = serializers.ChoiceField(
        choices=InsurancePolicyRecord.POLICY_OWNER_CHOICES
    )

    plan_type = serializers.ChoiceField(
        choices=InsurancePolicyRecord.PLAN_TYPE_CHOICES
    )

    # INDIVIDUAL FIELDS
    # for_whom = serializers.ChoiceField(
    #     choices=InsurancePolicyRecord.FOR_WHOM_CHOICES,
    #     required=False,
    #     default="self"
    # )
    dependant = serializers.IntegerField(required=False, allow_null=True)

    # FLOATER FIELDS
    is_self_included = serializers.BooleanField(required=False, default=True)
    self_uhid = serializers.CharField(required=False, allow_blank=True)
    floater_members = FloaterMemberInputSerializer(
        many=True, required=False
    )

    # core policy fields
    # policy_holder_name = serializers.CharField()
    policy_from = serializers.DateField()
    policy_to = serializers.DateField()

    type_of_insurance = serializers.ChoiceField(
        choices=InsurancePolicyRecord.TYPE_OF_INSURANCE_CHOICES
    )
    insurance_company = serializers.CharField()
    policy_number = serializers.CharField()
    policy_name = serializers.CharField()

    sum_assured = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )
    premium_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )

    tpa = serializers.CharField(required=False, allow_blank=True)
    nominee = serializers.CharField(required=False, allow_blank=True)

    # reminder config
    renewal_reminder_enabled = serializers.BooleanField(required=False)
    renewal_frequency = serializers.ChoiceField(
        choices=InsurancePolicyRecord.RENEWAL_FREQUENCY_CHOICES,
        required=False,
        allow_null=True,
    )
    renewal_reminder_type = serializers.ChoiceField(
        choices=InsurancePolicyRecord.REMINDER_TYPE_CHOICES,
        required=False,
        allow_null=True,
    )
    renewal_reminder_value = serializers.IntegerField(
        required=False, min_value=1
    )

    group_policy_details = serializers.CharField(
        required=False, allow_blank=True
    )
    policy_features = serializers.CharField(
        required=False, allow_blank=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    # keep_documents = serializers.ListField(
    #     child=serializers.IntegerField(), required=False
    # )

def validate(self, data):
    # date validation
    if data["policy_to"] < data["policy_from"]:
        raise ValidationError(
            {"policy_to": "Policy To date cannot be before Policy From date."}
        )

    owner_type = data.get("policy_owner_type")
    plan_type = data["plan_type"]

    # OWNER: COMPANY
    if owner_type == "company":
        data["for_whom"] = "self"
        data["dependant"] = None
        data["is_self_included"] = False
        return data

    # OWNER: SELF
    if owner_type == "self":
        data["for_whom"] = "self"
        data["dependant"] = None
        return data

    # OWNER: DEPENDANT
    if owner_type == "dependant":
        dep_id = data.get("dependant")
        if not dep_id:
            raise ValidationError({"dependant": "Dependant ID is required when policy_owner_type is 'dependant'."})

        data["for_whom"] = "dependant"
        return data

    # INDIVIDUAL PLAN
    if plan_type == "individual":
        for_whom = data.get("for_whom", "self")
        dep_id = data.get("dependant")

        if for_whom == "dependant" and dep_id is None:
            raise ValidationError({
                "dependant": "Dependants must be provided when for_whom is 'dependant'."
            })

        # clear floater-specific fields
        data["is_self_included"] = False
        data["self_uhid"] = ""
        data["floater_members"] = []

    # FLOATER PLAN
    elif plan_type == "floater":
        include_self = data.get("is_self_included", True)
        members = data.get("floater_members") or []

        if not include_self and not members:
            raise ValidationError({
                "floater_members": "Select at least self or one dependant for floater."
            })

        # clear individual-specific fields
        data["for_whom"] = "self"
        data["dependant"] = None

    # RENEWAL REMINDER VALIDATION
    if data.get("renewal_reminder_enabled"):
        if not data.get("renewal_frequency"):
            raise ValidationError({
                "renewal_frequency": "Required when renewal reminder is enabled."
            })
        if not data.get("renewal_reminder_type"):
            raise ValidationError({
                "renewal_reminder_type": "Required when renewal reminder is enabled."
            })
        if not data.get("renewal_reminder_value"):
            data["renewal_reminder_value"] = 1
    else:
        data["renewal_frequency"] = None
        data["renewal_reminder_type"] = None

    return data


class MedicalCardSerializer(serializers.ModelSerializer):
    document_for = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    file_url = serializers.FileField(source='file', read_only=True)
    insurance_company = serializers.CharField(source='policy.insurance_company', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)

    class Meta:
        model = InsurancePolicyDocument
        fields = [
            'id', 
            'document_for', 
            'name', 
            'file_url', 
            'insurance_company', 
            'policy_number',
            'created_at'
        ]

    def get_document_for(self, obj):
        # Return "Self" or "Dependant" based on policy configuration
        if obj.policy.for_whom == 'self':
            return "Self"
        return "Dependant"

    def get_name(self, obj):
        return obj.policy.policy_holder_name
