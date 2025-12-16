import json
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from apps.common.mixins.save_user_mixin import SaveUserMixin
from apps.dependants.models import Dependant
from apps.common.utils.profile_helper import filter_by_effective_user
from .models import HospitalizationRecord, HospitalizationDocument
from .serializers import (
    HospitalizationRecordSerializer,
    HospitalizationPayloadSerializer,
    HospitalizationDocumentSerializer,
)

class HospitalizationRecordViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HospitalizationRecordSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = HospitalizationRecord.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True
        ).order_by("-created_at")
        queryset = filter_by_effective_user(queryset, self.request)
        return queryset

    # CREATE - supports both JSON and multipart with optional documents
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Support both multipart (with "data" JSON field) and pure JSON
        if request.content_type and "multipart" in request.content_type:
            payload = self._extract_payload(request)
        else:
            payload = request.data

        serializer = HospitalizationPayloadSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        record = HospitalizationRecord(
            user=request.user,
            created_by=request.user,
            updated_by=request.user,
        )

        self._save_record_fields(record, validated)
        record.save()

        # Optional: Handle documents if provided during creation
        if request.FILES.getlist("documents"):
            for file in request.FILES.getlist("documents"):
                HospitalizationDocument.objects.create(
                    record=record,
                    file=file,
                    created_by=request.user,
                    updated_by=request.user
                )

        return Response(
            {
                "message": "Hospitalization record created successfully",
                "data": HospitalizationRecordSerializer(record).data
            },
            status=status.HTTP_201_CREATED
        )

    # UPDATE - supports both JSON and multipart with optional documents
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        record = self.get_object()

        if request.content_type and "multipart" in request.content_type:
            payload = self._extract_payload(request)
        else:
            payload = request.data

        serializer = HospitalizationPayloadSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        record.updated_by = request.user
        self._save_record_fields(record, validated)
        record.save()

        # Optional: Handle documents if provided during update
        if request.FILES.getlist("documents"):
            for file in request.FILES.getlist("documents"):
                HospitalizationDocument.objects.create(
                    record=record,
                    file=file,
                    created_by=request.user,
                    updated_by=request.user
                )

        return Response(
            {
                "message": "Hospitalization record updated successfully",
                "data": HospitalizationRecordSerializer(record).data
            },
            status=status.HTTP_200_OK
        )

    # DELETE (soft delete)
    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        record.deleted_at = timezone.now()
        record.save()
        return Response(
            {"message": "Hospitalization record deleted successfully"},
            status=status.HTTP_200_OK
        )

    # DOCUMENT MANAGEMENT ENDPOINTS

    @action(
        detail=True,
        methods=["post"],
        url_path="documents",
        parser_classes=[MultiPartParser]
    )
    def add_document(self, request, pk=None):
        # Upload one or more documents to a hospitalization record
        record = self.get_object()

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
            document = HospitalizationDocument.objects.create(
                record=record,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )
            created_documents.append(document)

        return Response(
            {
                "message": f"{len(created_documents)} document(s) uploaded successfully",
                "data": HospitalizationDocumentSerializer(
                    created_documents, many=True
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="documents/delete")
    def delete_document(self, request, pk=None):
        # Delete a document - requires 'document_id' in data or query params
        record = self.get_object()

        doc_id = request.data.get("document_id") or request.query_params.get("document_id")
        if not doc_id:
            raise ValidationError({"document_id": "This field is required"})

        document = get_object_or_404(
            HospitalizationDocument,
            id=doc_id,
            record=record,
            deleted_at__isnull=True,
        )

        document.delete()

        return Response(
            {"message": "Document deleted successfully"},
            status=status.HTTP_200_OK,
        )

    # Helper: Read JSON payload
    def _extract_payload(self, request):
        if "data" not in request.data:
            raise ValidationError({"error": "Missing 'data' field"})

        try:
            return json.loads(request.data["data"])
        except json.JSONDecodeError:
            raise ValidationError({"error": "Invalid JSON format in 'data' field"})

    # --------------------------
    # Save fields
    # --------------------------
    def _save_record_fields(self, record, validated):
        fields = [
            "hospitalization_type",
            "record_name",
            "hospital_name",
            "admitted_date",
            "discharged_date",
            "doctor_name",
            "notes",
            "for_whom",
        ]

        for f in fields:
            if f in validated:
                setattr(record, f, validated[f])

        # Dependant
        if "dependant" in validated:
            dep_id = validated["dependant"]
            if dep_id is None:
                record.dependant = None
            else:
                record.dependant = Dependant.objects.get(id=dep_id)

    # UTILITY ENDPOINTS

    @action(detail=False, methods=["get"])
    def choices(self, request):
        return Response(dict(HospitalizationRecord.HOSPITALIZATION_TYPE_CHOICES))
