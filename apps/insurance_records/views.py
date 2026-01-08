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
from apps.common.utils.profile_helper import filter_by_effective_user
from apps.dependants.models import Dependant

from .models import (
    InsurancePolicyRecord,
    InsuranceFloaterMember,
    InsurancePolicyDocument,
)
from .serializers import (
    InsurancePolicyRecordSerializer,
    InsurancePolicyPayloadSerializer,
    InsuranceFloaterMemberSerializer,
    InsurancePolicyDocumentSerializer,
    MedicalCardSerializer,

)


class InsurancePolicyRecordViewSet(SaveUserMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InsurancePolicyRecordSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # Queryset
    def get_queryset(self):
        qs = InsurancePolicyRecord.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True,
        ).order_by("-created_at")
        qs = filter_by_effective_user(qs, self.request)

        owner_type = self.request.query_params.get("policy_owner_type")
        if owner_type:
            qs = qs.filter(policy_owner_type=owner_type)

        who = self.request.query_params.get("who")
        if who == "self":
            qs = qs.filter(for_whom="self")
        elif who == "dependant":
            qs = qs.filter(for_whom="dependant")

        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if start:
            qs = qs.filter(policy_from__gte=start)
        if end:
            qs = qs.filter(policy_to__lte=end)

        company = self.request.query_params.get("company")
        if company:
            qs = qs.filter(insurance_company__icontains=company)

        return qs

    # Helpers
    def _extract_payload(self, request):
        if isinstance(request.data, dict) and "data" in request.data:
            try:
                return json.loads(request.data["data"])
            except json.JSONDecodeError:
                raise ValidationError({"data": "Invalid JSON in 'data' field"})
        return request.data

    def _save_main_fields(self, policy, data):
        editable_fields = [
            "policy_owner_type",
            "plan_type",
            "is_self_included",
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
        ]

        for field in editable_fields:
            if field in data:
                setattr(policy, field, data[field])

        # Set dependant + policy_holder_name
        owner = data.get("policy_owner_type")

        if owner == "dependant":
            dep = Dependant.objects.filter(
                id=data.get("dependant"),
                user=policy.user
            ).first()
            policy.dependant = dep
            policy.for_whom = "dependant"
            policy.policy_holder_name = dep.name if dep else ""

        elif owner == "self":
            policy.dependant = None
            policy.for_whom = "self"
            policy.policy_holder_name = getattr(policy.user, "name", policy.user.name)

        elif owner == "company":
            policy.dependant = None
            policy.for_whom = "self"
            policy.policy_holder_name = getattr(policy.user, "name", policy.user.name)

        # Floater policy-holder always set to user
        if policy.plan_type == "floater":
            policy.policy_holder_name = getattr(policy.user, "name", policy.user.name)

    def _save_floater_members(self, policy, validated, user):
        InsuranceFloaterMember.objects.filter(policy=policy).delete()

        if policy.plan_type != "floater":
            return

        # Add self member if enabled
        if validated.get("is_self_included", True):
            InsuranceFloaterMember.objects.create(
                policy=policy,
                is_self=True,
                uhid=validated.get("self_uhid") or "",
                created_by=user,
                updated_by=user
            )

        # Add dependant members
        for member in validated.get("floater_members", []):
            dep = Dependant.objects.filter(
                id=member.get("dependant_id"), user=policy.user
            ).first()

            if dep:
                InsuranceFloaterMember.objects.create(
                    policy=policy,
                    dependant=dep,
                    is_self=False,
                    uhid=member.get("uhid") or "",
                    created_by=user,
                    updated_by=user
                )

    def _save_documents(self, policy, validated, request):
        files = (
            request.FILES.getlist("documents")
            or request.FILES.getlist("files")
            or request.FILES.getlist("file")
        )

        for file in files:
            InsurancePolicyDocument.objects.create(
                policy=policy,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )

    # CRUD
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = self._extract_payload(request)
        ser = InsurancePolicyPayloadSerializer(data=payload)
        ser.is_valid(raise_exception=True)
        validated = ser.validated_data

        policy = InsurancePolicyRecord(
            user=request.user,
            created_by=request.user,
            updated_by=request.user,
        )

        self._save_main_fields(policy, validated)
        policy.save()

        self._save_floater_members(policy, validated, request.user)
        self._save_documents(policy, validated, request)

        return Response(
            {
                "message": "Insurance policy created successfully",
                "data": InsurancePolicyRecordSerializer(policy, context={"request": request}).data
            },
            status=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        policy = self.get_object()
        payload = self._extract_payload(request)

        ser = InsurancePolicyPayloadSerializer(data=payload)
        ser.is_valid(raise_exception=True)
        validated = ser.validated_data

        policy.updated_by = request.user
        self._save_main_fields(policy, validated)
        policy.save()

        self._save_floater_members(policy, validated, request.user)
        self._save_documents(policy, validated, request)

        return Response(
            {
                "message": "Insurance policy updated successfully",
                "data": InsurancePolicyRecordSerializer(policy, context={"request": request}).data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        policy = self.get_object()
        policy.deleted_at = timezone.now()
        policy.save()
        return Response({"message": "Insurance policy deleted successfully"})

    # DOCUMENT UPLOAD 
    @action(detail=True, methods=["post"], url_path="documents", parser_classes=[MultiPartParser])
    def add_document(self, request, pk=None):
        # Upload one or more documents to a policy
        policy = self.get_object()

        files = (
            request.FILES.getlist("documents")
            or request.FILES.getlist("files")
            or request.FILES.getlist("file")
        )

        if not files:
            raise ValidationError({"documents": "At least one file is required"})

        created_docs = []
        for file in files:
            doc = InsurancePolicyDocument.objects.create(
                policy=policy,
                file=file,
                created_by=request.user,
                updated_by=request.user,
            )
            created_docs.append(doc)

        return Response({
            "message": f"{len(created_docs)} document(s) uploaded successfully",
            "data": InsurancePolicyDocumentSerializer(created_docs, many=True).data
        })

    # DOCUMENT DELETE 
    @action(detail=True, methods=["delete"], url_path="documents/delete")
    def delete_document(self, request, pk=None):
        policy = self.get_object()

        doc_id = request.data.get("document_id") or request.query_params.get("document_id")
        if not doc_id:
            raise ValidationError({"document_id": "This field is required"})

        document = get_object_or_404(
            InsurancePolicyDocument,
            id=doc_id,
            policy=policy,
            deleted_at__isnull=True
        )

        document.delete()
        return Response({"message": "Document deleted successfully"})

    # CHOICES
    @action(detail=False, methods=["get"])
    def choices(self, request):
        return Response({
            "policy_owner_type": dict(InsurancePolicyRecord.POLICY_OWNER_CHOICES),
            "plan_type": dict(InsurancePolicyRecord.PLAN_TYPE_CHOICES),
            "type_of_insurance": dict(InsurancePolicyRecord.TYPE_OF_INSURANCE_CHOICES),
            "renewal_frequency": dict(InsurancePolicyRecord.RENEWAL_FREQUENCY_CHOICES),
            "renewal_reminder_type": dict(InsurancePolicyRecord.REMINDER_TYPE_CHOICES),
        })

    @action(detail=False, methods=["get"], url_path="medical_cards")
    def medical_cards(self, request):
        # Get list of uploaded medical cards (documents) for all active policies
        
        # Filter documents where the parent policy belongs to the user and is not deleted
        documents = InsurancePolicyDocument.objects.filter(
            policy__user=request.user,
            policy__deleted_at__isnull=True,
            deleted_at__isnull=True
        ).select_related('policy')
        
        serializer = MedicalCardSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)

