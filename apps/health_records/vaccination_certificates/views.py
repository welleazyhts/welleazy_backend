import json
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.common.mixins.save_user_mixin import SaveUserMixin
from apps.dependants.models import Dependant
from apps.common.utils.profile_helper import filter_by_effective_user
from .models import VaccinationCertificateRecord, VaccinationCertificateDocument
from .serializers import (
    VaccinationCertificateRecordSerializer,
    VaccinationPayloadSerializer,
    VaccinationCertificateDocumentSerializer
)


class VaccinationCertificateRecordViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VaccinationCertificateRecordSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = VaccinationCertificateRecord.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True
        ).order_by("-created_at")
        queryset = filter_by_effective_user(queryset, self.request)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = self._extract_payload(request)

        serializer = VaccinationPayloadSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        record = VaccinationCertificateRecord(
            user=request.user,
            created_by=request.user,
            updated_by=request.user
        )

        self._save_fields(record, validated)
        record.save()

        self._save_documents(record, validated, request)

        return Response(
            {
                "message": "Vaccination certificate record created successfully",
                "data": VaccinationCertificateRecordSerializer(record).data
            },
            status=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        record = self.get_object()
        payload = self._extract_payload(request)

        serializer = VaccinationPayloadSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        record.updated_by = request.user
        self._save_fields(record, validated)
        record.save()

        self._save_documents(record, validated, request)

        return Response(
            {
                "message": "Vaccination certificate record updated successfully",
                "data": VaccinationCertificateRecordSerializer(record).data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        record.deleted_at = timezone.now()
        record.save()
        return Response(
            {"message": "Vaccination certificate record deleted successfully"},
            status=status.HTTP_200_OK
        )

    # DOCUMENT MANAGEMENT ENDPOINTS (Separate)

    @action(detail=True, methods=["post"], url_path="documents", parser_classes=[MultiPartParser])
    def add_document(self, request, pk=None):
        # Upload one or more documents to a vaccination record
        record = self.get_object()
        
        files = request.FILES.getlist("documents") or request.FILES.getlist("files") or request.FILES.getlist("file")
        
        if not files:
            raise ValidationError({"documents": "At least one file is required"})
        
        created_documents = []
        for file in files:
            document = VaccinationCertificateDocument.objects.create(
                record=record,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )
            created_documents.append(document)
        
        return Response(
            {
                "message": f"{len(created_documents)} document(s) uploaded successfully",
                "data": VaccinationCertificateDocumentSerializer(created_documents, many=True).data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["delete"], url_path="documents/delete")
    def delete_document(self, request, pk=None):
        # Delete a document - requires 'document_id' in request data or query params
        record = self.get_object()
        
        doc_id = request.data.get('document_id') or request.query_params.get('document_id')
        if not doc_id:
            raise ValidationError({"document_id": "This field is required"})
        
        document = get_object_or_404(
            VaccinationCertificateDocument,
            id=doc_id,
            record=record,
            deleted_at__isnull=True
        )
        
        document.delete()
        
        return Response(
            {"message": "Document deleted successfully"},
            status=status.HTTP_200_OK
        )

    # HELPER METHODS

    def _extract_payload(self, request):
        # Extracts and parses JSON from 'data' field in multipart form
        if isinstance(request.data, dict) and "data" in request.data:
            try:
                return json.loads(request.data["data"])
            except json.JSONDecodeError:
                raise ValidationError({"error": "Invalid JSON format in 'data' field"})
        return request.data

    def _save_fields(self, record, validated):
        fields = [
            "vaccination_date",
            "vaccination_name",
            "vaccination_dose",
            "vaccination_center",
            "registration_id",
            "notes",
            "for_whom",
        ]

        for f in fields:
            if f in validated:
                setattr(record, f, validated[f])

        if "dependant" in validated:
            dep_id = validated["dependant"]
            record.dependant = None if dep_id is None else Dependant.objects.get(id=dep_id)

    def _save_documents(self, record, validated, request):
        # Save documents (create only - deletion via separate endpoint)
        files = request.FILES.getlist("documents") or request.FILES.getlist("files") or request.FILES.getlist("file")
        for file in files:
            VaccinationCertificateDocument.objects.create(
                record=record,
                file=file,
                created_by=request.user,
                updated_by=request.user
            )

    @action(detail=False, methods=["get"])
    def choices(self, request):
        return Response(dict(VaccinationCertificateRecord.VACCINE_TYPE_CHOICES))