from rest_framework import serializers
from apps.appointments.models import Appointment

class MyTransactionSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    transaction_id = serializers.CharField(source='payment_transaction_id')
    payment_method = serializers.CharField(source='payment_mode')

    class Meta:
        model = Appointment
        fields = [
            'id', 
            'transaction_id', 
            'title', 
            'amount', 
            'date', 
            'status', 
            'payment_method'
        ]

    def get_title(self, obj):
        if obj.item_type == 'doctor_appointment' and obj.doctor:
            return f"Consultation with {obj.doctor.doctor.full_name}"
        if obj.item_type == 'test' and obj.diagnostic_center:
            return f"Lab Test at {obj.diagnostic_center.name}"
        if obj.item_type == 'health_package':
            return "Health Package"
        if obj.item_type == 'sponsored_package':
            return "Sponsored Package"
        return obj.get_item_type_display()

    def get_amount(self, obj):
        # Prefer invoice amount if available
        if hasattr(obj, 'invoice_detail'):
            return float(obj.invoice_detail.total_amount)
        
        # Fallback to sum of items or consultation fee
        if obj.item_type == 'doctor_appointment' and obj.consultation_fee:
            return float(obj.consultation_fee)
        
        # For lab tests search in AppointmentItem
        items_total = sum(float(item.price or 0) for item in obj.items.all())
        return items_total if items_total > 0 else 0.0

    def get_date(self, obj):
        return obj.created_at.date()
