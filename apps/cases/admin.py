"""
Basic Case Admin for Customer Backend
Minimal admin for viewing cases. Full CRM admin is in welleazy_crm_backend.
"""
from django.contrib import admin
from .models import (
    Case, CaseItem, CaseRemark, CaseAssignment,
    CaseDocument, CaseStatusLog, ConsultationCase,
    CasePrescription, PrescriptionMedicine, CaseEscalation,
    QCReview, QCChecklist, QCChecklistResponse,
    TeleMERQuestionnaire, HealthCheckupRequest, CaseQueue
)


class CaseItemInline(admin.TabularInline):
    model = CaseItem
    extra = 0
    readonly_fields = ['final_price']


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """Basic Case admin - full CRM features in welleazy_crm_backend"""
    list_display = ['case_id', 'patient_name', 'service_type', 'status', 'created_at']
    list_filter = ['status', 'service_type', 'created_at']
    search_fields = ['case_id', 'patient_name', 'patient_phone']
    readonly_fields = ['case_id', 'created_at', 'updated_at', 'final_amount']
    ordering = ['-created_at']
    inlines = [CaseItemInline]


# Register other models with minimal config
@admin.register(CaseRemark)
class CaseRemarkAdmin(admin.ModelAdmin):
    list_display = ['case', 'remark_type', 'created_at']
    list_filter = ['remark_type']
    search_fields = ['case__case_id']


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ['case', 'document_type', 'file_name', 'created_at']
    list_filter = ['document_type']
    search_fields = ['case__case_id']


@admin.register(CaseStatusLog)
class CaseStatusLogAdmin(admin.ModelAdmin):
    list_display = ['case', 'from_status', 'to_status', 'created_at']
    list_filter = ['from_status', 'to_status']
    search_fields = ['case__case_id']


# Register models without custom admin (they'll be managed in CRM)
admin.site.register(CaseItem)
admin.site.register(CaseAssignment)
admin.site.register(ConsultationCase)
admin.site.register(CasePrescription)
admin.site.register(PrescriptionMedicine)
admin.site.register(CaseEscalation)
admin.site.register(QCReview)
admin.site.register(QCChecklist)
admin.site.register(QCChecklistResponse)
admin.site.register(TeleMERQuestionnaire)
admin.site.register(HealthCheckupRequest)
admin.site.register(CaseQueue)
