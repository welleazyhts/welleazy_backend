from rest_framework import serializers
from apps.dependants.models import Dependant
from apps.dependants.serializers import DependantSerializer
from apps.common.serializers.dependant_mixin import DependantResolverMixin
from .models import HealthAssessment
from .models import FamilyIllnessRecord
from django.contrib.auth import get_user_model

class HealthAssessmentListSerializer(serializers.ModelSerializer):

    dependant_data = DependantSerializer(source="dependant", read_only=True)
    for_whom = serializers.SerializerMethodField()
    # risk_label = serializers.SerializerMethodField()
    report_url = serializers.SerializerMethodField()

    class Meta:
        model = HealthAssessment
        fields = [
            "id",
            "created_at",
            "status",
            "for_whom",
            "dependant_data",
            # "total_score",
            # "risk_category",
            # "risk_label",
            "report_url",
        ]

    def get_for_whom(self, obj):
        if obj.for_whom == "self":
            user = self.context["request"].user
            return {
                "type": "self",
                "name": user.name or user.username
            }
        if obj.for_whom == "dependant" and obj.dependant:
            return {
                "type": "dependant",
                "name": obj.dependant.name
            }
        return {"type": "unknown", "name": ""}


    # def get_risk_label(self, obj):
    #     return obj.get_risk_category_display() if obj.risk_category else None

    def get_report_url(self, obj):
        request = self.context.get("request")
        if obj.report_file and request:
            return request.build_absolute_uri(obj.report_file.url)
        return None

class FamilyIllnessRecordSerializer(serializers.ModelSerializer):
    dependant_data = DependantSerializer(source="dependant", read_only=True)

    class Meta:
        model = FamilyIllnessRecord
        fields = ["id", "dependant", "dependant_data", "disease"]


class HealthAssessmentSerializer(DependantResolverMixin, serializers.ModelSerializer):

    #Full detail serializer (used for retrieve, update, submit).
    #dependant_data is provided by DependantResolverMixin:
    #else -> returns dependant data
    report_url = serializers.SerializerMethodField()
    family_illness_records = FamilyIllnessRecordSerializer(many=True, required=False)

    class Meta:
        model = HealthAssessment
        exclude = ("total_score", "risk_category")
        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "report_file",
            "status",
        )
        
    def validate(self, data):
        
        # ---- Presenting Illness ----
        if "presenting_illness" in data:
            if data.get("presenting_illness") == "other":
                if not data.get("presenting_illness_other"):
                    raise serializers.ValidationError({
                        "presenting_illness_other": "Please specify the illness."
                    })
            else:
                data["presenting_illness_other"] = ""

        # ------------------ Eating habits validation ------------------
        if "is_veg" in data:
            if data.get("is_veg") is False and not data.get("non_veg_freq"):
                raise serializers.ValidationError({
                    "non_veg_freq": "Required when user is Non-Vegetarian."
                })
            if data.get("is_veg") is True:
                data["non_veg_freq"] = ""

        # ------------------ Past history validation ------------------
        if "chronic_illness" in data:
            if data.get("chronic_illness") is True and not data.get("chronic_illness_details"):
                raise serializers.ValidationError({
                    "chronic_illness_details": "Additional information is required."
                })
            if data.get("chronic_illness") is False:
                data["chronic_illness_details"] = ""

        if "surgery_history" in data:
            if data.get("surgery_history") is True and not data.get("surgery_history_details"):
                raise serializers.ValidationError({
                    "surgery_history_details": "Additional information is required."
                })
            if data.get("surgery_history") is False:
                data["surgery_history_details"] = ""
                
        # ---- Midnight wake-up reasons ----
        if "wakeup_midnight" in data:
            if data.get("wakeup_midnight") is True and not data.get("wakeup_midnight_reasons"):
                raise serializers.ValidationError({
                    "wakeup_midnight_reasons": "Select at least one reason."
                })
            if data.get("wakeup_midnight") is False:
                data["wakeup_midnight_reasons"] = []
                
        # ---- Alcohol consumption details ----
        alcohol_current = data.get("alcohol_current")
        alcohol_past = data.get("alcohol_past")

        # CASE 1: CURRENT DRINKER
        if alcohol_current is True:
            required_fields = ["alcohol_frequency", "alcohol_quantity", "alcohol_duration"]
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: "This field is required for current drinkers."
                    })

            # Automatically reset past drinking info
            data["alcohol_past"] = False
            data["alcohol_quit_period"] = None

        # CASE 2: PAST DRINKER
        elif alcohol_current is False and alcohol_past is True:

            if not data.get("alcohol_quit_period"):
                raise serializers.ValidationError({
                    "alcohol_quit_period": "Required when alcohol was consumed in the past."
                })

            # Clear current drinker details
            data["alcohol_frequency"] = None
            data["alcohol_quantity"] = None
            data["alcohol_duration"] = None

        # CASE 3: NEVER DRANK
        elif alcohol_current is False and alcohol_past is False:

            # Clear everything
            data["alcohol_frequency"] = None
            data["alcohol_quantity"] = None
            data["alcohol_duration"] = None
            data["alcohol_quit_period"] = None
            
        # ---- Tobacco / Smoking validation ----
        tobacco_current = data.get("tobacco_current")
        tobacco_quit = data.get("tobacco_quit")

        # CASE 1 → CURRENT SMOKER
        if tobacco_current is True:

            required_fields = ["tobacco_type", "tobacco_duration", "tobacco_planning_quit"]
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: "This field is required for current tobacco users."
                    })

            # Past quit is not applicable
            data["tobacco_quit"] = False
            data["tobacco_quit_period"] = None

        # CASE 2 → PAST SMOKER (QUIT)
        elif tobacco_current is False and tobacco_quit is True:

            if not data.get("tobacco_quit_period"):
                raise serializers.ValidationError({
                    "tobacco_quit_period": "Required when user has quit tobacco."
                })

            # Clear current smoker details
            data["tobacco_type"] = None
            data["tobacco_duration"] = None
            data["tobacco_planning_quit"] = None

        # CASE 3 → NEVER SMOKED
        elif tobacco_current is False and tobacco_quit is False:

            data["tobacco_type"] = None
            data["tobacco_duration"] = None
            data["tobacco_planning_quit"] = None
            data["tobacco_quit_period"] = None
            
        # ---- Family chronic illness validation ----
        if "family_chronic_illness" in data:
            if data.get("family_chronic_illness") is True:
                records = self.initial_data.get("family_illness_records")
                if not records:
                    raise serializers.ValidationError({
                        "family_illness_records": "At least one family record must be added."
                    })
            else:
                data["family_illness_records"] = []
                
        # ---- Bowel / bladder validation ----
        if "difficulty_urine" in data:
            if data.get("difficulty_urine") is True:
                if not self.initial_data.get("difficulty_urine_reasons"):
                    raise serializers.ValidationError({
                        "difficulty_urine_reasons": "Select at least one reason."
                    })
            else:
                data["difficulty_urine_reasons"] = []
                
        # ---- Employee wellness validation ----
        if "work_stress_affecting_life" in data:

            if data.get("work_stress_affecting_life") is True:
                # must provide reasons
                reasons = self.initial_data.get("work_stress_reasons")
                if not reasons:
                    raise serializers.ValidationError({
                        "work_stress_reasons": "Select at least one reason for work stress."
                    })

            if data.get("work_stress_affecting_life") is False:
                # clear reasons when NO
                data["work_stress_reasons"] = []


        return data
    
    
    def update(self, instance, validated_data):
        family_records = validated_data.pop("family_illness_records", None)

        instance = super().update(instance, validated_data)

        # If chronic false → wipe all
        if validated_data.get("family_chronic_illness") is False:
            FamilyIllnessRecord.objects.filter(hra=instance).delete()
            return instance

        # If chronic true → and records provided
        if family_records is not None:

            # Delete existing
            FamilyIllnessRecord.objects.filter(hra=instance).delete()

            for rec in family_records:

                dep_value = rec.get("dependant")

                # FIX: Extract ID
                if isinstance(dep_value, Dependant):
                    dep_id = dep_value.id
                else:
                    dep_id = dep_value   # should be integer

                FamilyIllnessRecord.objects.create(
                    hra=instance,
                    dependant_id=dep_id,
                    disease=rec["disease"]
                )

        return instance




    def get_report_url(self, obj):
        request = self.context.get("request")
        if obj.report_file and request:
            return request.build_absolute_uri(obj.report_file.url)
        return None


class HealthAssessmentCreateSerializer(serializers.Serializer):
    # Used only when starting a new assessment.
    # Step 1–2 selection: self vs dependant.
    for_whom = serializers.ChoiceField(
        choices=["self", "dependant"],
        required=True
    )
    dependant = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        for_whom = data.get("for_whom")
        dep_id = data.get("dependant")

        if for_whom == "dependant" and dep_id is None:
            raise serializers.ValidationError({
                "dependant": "Dependants must be provided when for_whom is 'dependant'."
            })

        return data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        for_whom = validated_data.get("for_whom")
        dep_id = validated_data.get("dependant")

        dependant = None
        if for_whom == "dependant" and dep_id:
            dependant = Dependant.objects.filter(
                id=dep_id,
                user=user
            ).first()

        hra = HealthAssessment.objects.create(
            user=user,
            for_whom=for_whom,
            dependant=dependant,
            current_step=3,  # next screen after basic details
            status="in_process",
            created_by=user,
            updated_by=user,
        )
        return hra

