"""
Customer-facing Case Views
API endpoints for customers to view and manage their cases.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Case, CaseRemark, CaseDocument
from .serializers import (
    CaseListSerializer, CaseDetailSerializer, CaseCreateSerializer,
    CaseRemarkSerializer, CaseRemarkCreateSerializer,
    CaseDocumentSerializer
)


class CustomerCaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for customers to view and manage their own cases.
    Customers can only see their own cases.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'service_type': ['exact', 'in'],
        'scheduled_date': ['exact', 'gte', 'lte'],
    }
    search_fields = ['case_id', 'patient_name']
    ordering_fields = ['created_at', 'scheduled_date', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Only return cases belonging to the current user"""
        return Case.objects.filter(user=self.request.user).select_related(
            'vendor', 'diagnostic_center'
        ).prefetch_related('items', 'documents')

    def get_serializer_class(self):
        if self.action == 'list':
            return CaseListSerializer
        elif self.action == 'create':
            return CaseCreateSerializer
        return CaseDetailSerializer

    def perform_create(self, serializer):
        """Set the user and source when creating a case"""
        serializer.save(
            user=self.request.user,
            source='web',
            created_by=self.request.user,
            updated_by=self.request.user
        )

    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """Get status history for a case"""
        case = self.get_object()
        from .models import CaseStatusLog
        from .serializers import CaseStatusLogSerializer

        logs = CaseStatusLog.objects.filter(case=case).order_by('-created_at')
        serializer = CaseStatusLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """Add a document to a case"""
        case = self.get_object()
        serializer = CaseDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = CaseDocument.objects.create(
            case=case,
            **serializer.validated_data
        )

        return Response(CaseDocumentSerializer(document).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a case (only if not yet started)"""
        case = self.get_object()

        if case.status not in ['new', 'assigned', 'scheduled']:
            return Response(
                {'error': 'Cannot cancel case that is already in progress or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', 'Cancelled by customer')

        # Update case status
        old_status = case.status
        case.status = 'cancelled'
        case.save()

        # Log the status change
        from .models import CaseStatusLog
        CaseStatusLog.objects.create(
            case=case,
            from_status=old_status,
            to_status='cancelled',
            changed_by=request.user,
            reason=reason
        )

        # Add remark
        CaseRemark.objects.create(
            case=case,
            remark_type='status_change',
            remark=f"Case cancelled by customer. Reason: {reason}",
            is_internal=False
        )

        return Response(CaseDetailSerializer(case).data)

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule a case"""
        case = self.get_object()

        if case.status not in ['new', 'assigned', 'scheduled']:
            return Response(
                {'error': 'Cannot reschedule case that is already in progress or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_date = request.data.get('scheduled_date')
        new_time = request.data.get('scheduled_time')
        reason = request.data.get('reason', 'Rescheduled by customer')

        if not new_date:
            return Response(
                {'error': 'New scheduled date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from datetime import datetime
        try:
            new_scheduled_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_scheduled_time = None
        if new_time:
            try:
                new_scheduled_time = datetime.strptime(new_time, '%H:%M').time()
            except ValueError:
                return Response(
                    {'error': 'Invalid time format. Use HH:MM'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        old_date = case.scheduled_date
        case.scheduled_date = new_scheduled_date
        case.scheduled_time = new_scheduled_time
        case.save()

        # Add remark
        CaseRemark.objects.create(
            case=case,
            remark_type='general',
            remark=f"Rescheduled from {old_date} to {new_scheduled_date}. Reason: {reason}",
            is_internal=False
        )

        return Response(CaseDetailSerializer(case).data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming scheduled cases"""
        today = timezone.now().date()
        upcoming = self.get_queryset().filter(
            scheduled_date__gte=today,
            status__in=['new', 'assigned', 'scheduled']
        ).order_by('scheduled_date', 'scheduled_time')

        serializer = CaseListSerializer(upcoming, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get completed/cancelled cases"""
        completed = self.get_queryset().filter(
            status__in=['completed', 'cancelled']
        ).order_by('-completed_at', '-updated_at')

        serializer = CaseListSerializer(completed, many=True)
        return Response(serializer.data)


class CustomerCaseDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for case documents - customer facing"""
    serializer_class = CaseDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CaseDocument.objects.filter(
            case_id=self.kwargs.get('case_pk'),
            case__user=self.request.user
        )
