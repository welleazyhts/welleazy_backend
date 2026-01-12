from datetime import date

from django.utils import timezone
from django.http import FileResponse

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins.save_user_mixin import SaveUserMixin
from apps.dependants.models import Dependant
from django.utils.timezone import localtime

from .services import HealthAssessmentReportService
from apps.common.utils.profile_helper import filter_by_effective_user

from .models import FamilyIllnessRecord, HealthAssessment
from .serializers import (
    HealthAssessmentSerializer,
    HealthAssessmentCreateSerializer,
    HealthAssessmentListSerializer,
)


def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class HealthAssessmentViewSet(SaveUserMixin, viewsets.ModelViewSet):

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            HealthAssessment.objects
            .filter(user=self.request.user, deleted_at__isnull=True)
            .select_related("dependant")
            .order_by("-created_at")
        )
        queryset = filter_by_effective_user(queryset, self.request)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return HealthAssessmentListSerializer
        if self.action == "create":
            return HealthAssessmentCreateSerializer
        return HealthAssessmentSerializer

    # create: start new HRA
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        hra = serializer.save()
        out = HealthAssessmentSerializer(
            hra, context={"request": request}
        ).data
        return Response(
            {
                "message": "Health assessment created successfully",
                "data": out
            },
            status=status.HTTP_201_CREATED
        )
    # partial update (save any step)
    def partial_update(self, request, *args, **kwargs):

        instance = self.get_object()
        step = request.data.get("current_step", instance.current_step)

        serializer = HealthAssessmentSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        records = request.data.get("family_illness_records")

        # Remove all existing records if user said "No"
        if request.data.get("family_chronic_illness") is False:
            instance.family_illness_records.all().delete()

        # If user submitted records
        elif records:
            instance.family_illness_records.all().delete()
            new_records = [
                FamilyIllnessRecord(
                    hra=instance,
                    dependant_id=r["dependant"],
                    disease=r["disease"]
                ) for r in records
            ]
            FamilyIllnessRecord.objects.bulk_create(new_records)

        hra = serializer.save(
            updated_by=request.user,
            current_step=step,
        )

        return Response(
            {
                "message": "Health assessment updated successfully",
                "data": HealthAssessmentSerializer(
                    hra, context={"request": request}
                ).data
            },
            status=status.HTTP_200_OK
        )

    # soft delete
    def destroy(self, request, *args, **kwargs):
        hra = self.get_object()
        hra.deleted_at = timezone.now()
        hra.save(update_fields=["deleted_at"])
        return Response(
            {"message": "Health assessment deleted successfully"},
            status=status.HTTP_200_OK
        )
        
    # prefill (self / dependant)
    @action(detail=False, methods=["get"])
    def prefill(self, request):

        dep_id = request.query_params.get("dependant_id")

        # SELF PREFILL (AUTH USER)
        if not dep_id:
            user = request.user
            profile = getattr(user, "profile", None)

            gender = getattr(profile, "gender", None)
            dob = getattr(profile, "dob", None)
            age = calculate_age(dob)

            return Response({
                "type": "self",
                "id": user.id,
                "name": getattr(user, "name", None) or user.username,
                "gender": gender,
                "dob": dob,
                "age": age,
            })

        # DEPENDANT PREFILL
        dep = Dependant.objects.filter(
            id=dep_id,
            user=request.user
        ).select_related("relationship").first()

        if not dep:
            return Response(
                {"detail": "Invalid dependant_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dob = dep.dob
        age = calculate_age(dob)

        rel_name = dep.relationship.name if dep.relationship else None

        return Response({
            "type": "dependant",
            "id": dep.id,
            "name": dep.name,
            "gender": dep.gender,
            "dob": dep.dob,
            "age": age,
            "relationship": rel_name,
        })

    # choices for dropdowns/sliders
    @action(detail=False, methods=["get"])
    def choices(self, request):
        m = HealthAssessment
        return Response({
            "mood_today": dict(m.MOOD_CHOICES),
            "height_unit": dict(m.HEIGHT_UNIT_CHOICES),
            "eat_frequency": dict(m.FREQ5_CHOICES),
            "water_intake": dict(m.WATER_CHOICES),
            "sleep_hours": dict(m.SLEEP_HOURS_CHOICES),
            "checkup_frequency": dict(m.CHECKUP_FREQ_CHOICES),
            "fitness_duration": dict(m.DURATION4_CHOICES),
            "other_activity": dict(m.OTHER_ACTIVITY_CHOICES),
            "risk_category": dict(m.RISK_CATEGORY_CHOICES),
            "wakeup_midnight_reasons": dict(m.WAKEUP_REASON_CHOICES),
            "alcohol_frequency": dict(m.ALCOHOL_FREQUENCY_CHOICES),
            "alcohol_duration": dict(m.ALCOHOL_DURATION_CHOICES),
            "alcohol_quit_period": dict(m.ALCOHOL_QUIT_CHOICES),
            "family_disease_list": dict(FamilyIllnessRecord.DISEASE_CHOICES),
            "urine_difficulty_reasons": dict(m.URINE_DIFFICULTY_REASON_CHOICES),
            "work_stress_reasons": dict(m.WORK_STRESS_REASON_CHOICES),
        })

    # final submit
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):

        hra = self.get_object()

        # self._calculate_score(hra)
        # self._calculate_score(hra)
        HealthAssessmentReportService.generate_report_file(hra)

        hra.status = "active"
        hra.current_step = 15
        hra.updated_by = request.user
        hra.save()

        return Response(
            HealthAssessmentSerializer(
                hra, context={"request": request}
            ).data
        )

    @action(detail=True, methods=["get"])
    def download_report(self, request, pk=None):
        hra = self.get_object()
        if not hra.report_file:
            return Response(
                {"detail": "Report not generated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return FileResponse(
            hra.report_file.open("rb"),
            as_attachment=True,
            filename=hra.report_file.name.split("/")[-1],
        )



