import json
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from apps.consultation_filter.models import DoctorSpeciality
from apps.dependants.models import Dependant
from apps.common.utils.profile_helper import filter_by_effective_user
from .models import PrescriptionRecord, PrescriptionParameter, PrescriptionDocument
from .serializers import (
    PrescriptionRecordSerializer,
    RecordPayloadSerializer,
    PrescriptionParameterSerializer,
    PrescriptionDocumentSerializer
)
from apps.common.mixins.save_user_mixin import SaveUserMixin


class PrescriptionRecordViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrescriptionRecordSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = PrescriptionRecord.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True
        )
        queryset = filter_by_effective_user(queryset, self.request)
        return queryset.order_by("-created_at")

    # CREATE
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = self._extract_payload(request)

        serializer = RecordPayloadSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        record = PrescriptionRecord(
            user=request.user,
            created_by=request.user,
            updated_by=request.user,
        )

        self._save_record_fields(record, validated)
        record.save()

        self._save_parameters(record, validated, request)
        self._save_documents(record, validated, request)

        return Response(
            {
                "message": "Prescription record created successfully",
                "data": PrescriptionRecordSerializer(record).data
            },
            status=status.HTTP_201_CREATED
        )

    # UPDATE
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        record = self.get_object()
        payload = self._extract_payload(request)

        serializer = RecordPayloadSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        record.updated_by = request.user
        self._save_record_fields(record, validated)
        record.save()

        self._save_parameters(record, validated, request)
        self._save_documents(record, validated, request)

        return Response(
            {
                "message": "Prescription record updated successfully",
                "data": PrescriptionRecordSerializer(record).data
            },
            status=status.HTTP_200_OK
        )

    # DELETE (Soft delete)
    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        record.deleted_at = timezone.now()
        record.save()
        return Response(
            {"message": "Prescription record deleted successfully"},
            status=status.HTTP_200_OK
        )

    # PARAMETER MANAGEMENT ENDPOINTS (Separate)

    @action(detail=True, methods=["post"], url_path="parameters")
    def add_parameter(self, request, pk=None):
        # Add a new parameter to a prescription record
        record = self.get_object()
        
        serializer = PrescriptionParameterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        parameter = PrescriptionParameter.objects.create(
            record=record,
            created_by=request.user,
            updated_by=request.user,
            **serializer.validated_data
        )
        
        return Response(
            {
                "message": "Parameter added successfully",
                "data": PrescriptionParameterSerializer(parameter).data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["put", "patch"], url_path="parameters/update")
    def update_parameter(self, request, pk=None):
        # Update an existing parameter - requires 'parameter_id' in request data
        record = self.get_object()
        
        param_id = request.data.get('parameter_id')
        if not param_id:
            raise ValidationError({"parameter_id": "This field is required"})
        
        parameter = get_object_or_404(
            PrescriptionParameter,
            id=param_id,
            record=record,
            deleted_at__isnull=True
        )
        
        serializer = PrescriptionParameterSerializer(
            parameter,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        for key, value in serializer.validated_data.items():
            setattr(parameter, key, value)
        
        parameter.updated_by = request.user
        parameter.save()
        
        return Response(
            {
                "message": "Parameter updated successfully",
                "data": PrescriptionParameterSerializer(parameter).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["delete"], url_path="parameters/delete")
    def delete_parameter(self, request, pk=None):
        # Delete a parameter - requires 'parameter_id' in request data or query params
        record = self.get_object()
        
        param_id = request.data.get('parameter_id') or request.query_params.get('parameter_id')
        if not param_id:
            raise ValidationError({"parameter_id": "This field is required"})
        
        parameter = get_object_or_404(
            PrescriptionParameter,
            id=param_id,
            record=record,
            deleted_at__isnull=True
        )
        
        parameter.delete()
        
        return Response(
            {"message": "Parameter deleted successfully"},
            status=status.HTTP_200_OK
        )

    # DOCUMENT MANAGEMENT ENDPOINTS (Separate)

    @action(detail=True, methods=["post"], url_path="documents", parser_classes=[MultiPartParser])
    def add_document(self, request, pk=None):
        # Upload one or more documents to a prescription record
        record = self.get_object()
        
        files = request.FILES.getlist("documents") or request.FILES.getlist("files") or request.FILES.getlist("file")
        
        if not files:
            raise ValidationError({"documents": "At least one file is required"})
        
        created_documents = []
        for file in files:
            document = PrescriptionDocument.objects.create(
                record=record,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )
            created_documents.append(document)
        
        return Response(
            {
                "message": f"{len(created_documents)} document(s) uploaded successfully",
                "data": PrescriptionDocumentSerializer(created_documents, many=True).data
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
            PrescriptionDocument,
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

    def _save_record_fields(self, record, validated):
        # Save main record fields
        simple_fields = [
            "record_type",
            "record_name",
            "record_date",
            "doctor_name",
            "reason",
            "for_whom",
        ]

        for f in simple_fields:
            if f in validated:
                setattr(record, f, validated[f])

        # Foreign key: doctor_specialization
        if "doctor_specialization" in validated:
            spec_id = validated["doctor_specialization"]

            if spec_id is None:
                record.doctor_specialization = None
            else:
                try:
                    record.doctor_specialization = DoctorSpeciality.objects.get(id=spec_id)
                except DoctorSpeciality.DoesNotExist:
                    raise ValidationError({
                        "doctor_specialization": f"Invalid specialization id: {spec_id}"
                    })
        
            # Foreign key: dependant      
        if "dependant" in validated:
            dep_id = validated["dependant"]

            if dep_id is None:
                record.dependant = None
            else:
                try:
                    record.dependant = Dependant.objects.get(id=dep_id, user=self.request.user)
                except Dependant.DoesNotExist:
                    raise ValidationError({"dependant": f"Invalid dependant id for this user: {dep_id}"})

    def _save_parameters(self, record, validated, request):
        # Save parameters (create/delete) - supports both keep_parameters and parameters
        # Only handle deletion if keep_parameters is explicitly provided
        if "keep_parameters" in validated:
            keep_ids = validated["keep_parameters"]
            PrescriptionParameter.objects.filter(record=record).exclude(id__in=keep_ids).delete()

        # Create new ones
        new_params = validated.get("parameters", [])
        for param in new_params:
            PrescriptionParameter.objects.create(
                record=record,
                parameter_name=param["parameter_name"],
                result=param.get("result"),
                unit=param.get("unit"),
                start_range=param.get("start_range"),
                end_range=param.get("end_range"),
                created_by=request.user,
                updated_by=request.user,
            )

    def _save_documents(self, record, validated, request):
        # Save documents (create/delete)
        # Only handle deletion if keep_documents is explicitly provided
        if "keep_documents" in validated:
            keep_ids = validated["keep_documents"]
            PrescriptionDocument.objects.filter(record=record).exclude(id__in=keep_ids).delete()

        for file in request.FILES.getlist("documents"):
            PrescriptionDocument.objects.create(
                record=record,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )

    # UTILITY ENDPOINTS

    @action(detail=False, methods=["get"])
    def prescription_type_choices(self, request):
        # Get available prescription type choices
        return Response(dict(PrescriptionRecord.PRESCRIPTION_TYPE_CHOICES))

    @action(detail=False, methods=["get"])
    def doctor_specializations(self, request):
        # Get list of active doctor specializations
        from apps.consultation_filter.models import DoctorSpeciality
        from apps.consultation_filter.serializers import DoctorSpecialitySerializer

        data = DoctorSpecialitySerializer(
            DoctorSpeciality.objects.filter(is_active=True),
            many=True
        ).data
        return Response(data)