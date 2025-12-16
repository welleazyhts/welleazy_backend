import json
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.common.mixins.save_user_mixin import SaveUserMixin
from .models import MedicineReminder, MedicineReminderTime, MedicineReminderDocument
from .serializers import (
    MedicineReminderSerializer,
    MedicineReminderPayloadSerializer,
    MedicineReminderDocumentSerializer,
)


class MedicineReminderViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicineReminderSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = MedicineReminder.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True,
        ).order_by("-created_at")

        start = self.request.query_params.get("start_date")
        end = self.request.query_params.get("end_date")
        if start:
            qs = qs.filter(start_date__gte=start)
        if end:
            qs = qs.filter(end_date__lte=end)
        return qs

    # ------------ helpers ------------
    def _extract_payload(self, request):
        # Supports both:
        # - multipart with 'data' field (stringified JSON)
        # - pure JSON body
        if isinstance(request.data, dict) and "data" in request.data:
            try:
                return json.loads(request.data["data"])
            except json.JSONDecodeError:
                raise ValidationError({"data": "Invalid JSON in 'data' field"})
        return request.data

    def _save_main_fields(self, reminder, data):
        fields = [
            "medicine_name", "medicine_type",
            "duration_value", "duration_unit",
            "start_date", "end_date",
            "frequency_type", "intake_frequency",
            "interval_type", "interval_start_time", "interval_end_time",
            "dosage_value", "dosage_unit",
            "doctor_name", "appointment_reminder_date",
            "current_inventory", "remind_when_inventory", "medicines_left",
        ]
        for f in fields:
            if f in data:
                setattr(reminder, f, data[f])

    def _save_schedule_times(self, reminder, data):
        MedicineReminderTime.objects.filter(reminder=reminder).delete()
        if reminder.frequency_type != "fixed_times":
            return

        for t in data.get("schedule_times", []):
            MedicineReminderTime.objects.create(
                reminder=reminder,
                time=t["time"],
                meal_relation=t["meal_relation"],
                created_by=reminder.created_by,
                updated_by=reminder.updated_by,
            )

    # ------------ create ------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = self._extract_payload(request)
        payload_ser = MedicineReminderPayloadSerializer(data=payload)
        payload_ser.is_valid(raise_exception=True)
        validated = payload_ser.validated_data

        reminder = MedicineReminder(
            user=request.user,
            created_by=request.user,
            updated_by=request.user,
        )
        self._save_main_fields(reminder, validated)
        reminder.save()

        self._save_schedule_times(reminder, validated)

        # Optional: Handle documents if provided during creation
        if request.FILES.getlist("documents"):
            for file in request.FILES.getlist("documents"):
                MedicineReminderDocument.objects.create(
                    reminder=reminder,
                    file=file,
                    created_by=request.user,
                    updated_by=request.user
                )

        return Response(
            {
                "message": "Medicine reminder created successfully",
                "data": MedicineReminderSerializer(reminder).data
            },
            status=status.HTTP_201_CREATED,
        )

    # ------------ update ------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        reminder = self.get_object()
        payload = self._extract_payload(request)
        payload_ser = MedicineReminderPayloadSerializer(data=payload)
        payload_ser.is_valid(raise_exception=True)
        validated = payload_ser.validated_data

        reminder.updated_by = request.user
        self._save_main_fields(reminder, validated)
        reminder.save()

        self._save_schedule_times(reminder, validated)

        # Optional: Handle documents if provided during update
        if request.FILES.getlist("documents"):
            for file in request.FILES.getlist("documents"):
                MedicineReminderDocument.objects.create(
                    reminder=reminder,
                    file=file,
                    created_by=request.user,
                    updated_by=request.user
                )

        return Response(
            {
                "message": "Medicine reminder updated successfully",
                "data": MedicineReminderSerializer(reminder).data
            },
            status=status.HTTP_200_OK
        )

    # ------------ soft delete ------------
    def destroy(self, request, *args, **kwargs):
        reminder = self.get_object()
        reminder.deleted_at = timezone.now()
        reminder.save()
        return Response(
            {"message": "Medicine reminder deleted successfully"},
            status=status.HTTP_200_OK
        )

    # ------------ DOCUMENT MANAGEMENT ENDPOINTS ------------

    @action(
        detail=True,
        methods=["post"],
        url_path="documents",
        parser_classes=[MultiPartParser]
    )
    def add_document(self, request, pk=None):
        # Upload one or more documents to a medicine reminder
        reminder = self.get_object()

        # support 'documents' OR 'file/files' keys
        files = (
            request.FILES.getlist("documents")
            or request.FILES.getlist("files")
            or request.FILES.getlist("file")
        )

        if not files:
            raise ValidationError({"documents": "At least one file is required"})

        created_documents = []
        for file in files:
            document = MedicineReminderDocument.objects.create(
                reminder=reminder,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )
            created_documents.append(document)

        return Response(
            {
                "message": f"{len(created_documents)} document(s) uploaded successfully",
                "data": MedicineReminderDocumentSerializer(
                    created_documents, many=True
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="documents/delete")
    def delete_document(self, request, pk=None):
        # Delete a document - requires 'document_id' in data or query params
        reminder = self.get_object()

        doc_id = request.data.get("document_id") or request.query_params.get("document_id")
        if not doc_id:
            raise ValidationError({"document_id": "This field is required"})

        document = get_object_or_404(
            MedicineReminderDocument,
            id=doc_id,
            reminder=reminder,
            deleted_at__isnull=True,
        )

        document.delete()

        return Response(
            {"message": "Document deleted successfully"},
            status=status.HTTP_200_OK,
        )

    # ------------ CHOICES ENDPOINT ------------

    @action(detail=False, methods=["get"])
    def choices(self, request):
        return Response({
            "medicine_type": dict(MedicineReminder.MEDICINE_TYPE_CHOICES),
            "frequency_type": dict(MedicineReminder.FREQUENCY_TYPE_CHOICES),
            "intake_frequency": dict(MedicineReminder.INTAKE_FREQUENCY_CHOICES),
            "interval_type": dict(MedicineReminder.INTERVAL_TYPE_CHOICES),
            "duration_unit": dict(MedicineReminder.DURATION_UNIT_CHOICES),
            "dosage_unit": dict(MedicineReminder.DOSAGE_UNIT_CHOICES),
            "meal_relation": dict(MedicineReminder.MEAL_RELATION_CHOICES),
        })
