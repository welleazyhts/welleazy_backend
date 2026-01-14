from django.shortcuts import render

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import AppointmentInvoice
from reportlab.pdfgen import canvas
from django.http import FileResponse
from io import BytesIO


class AppointmentInvoiceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        invoice = get_object_or_404(AppointmentInvoice,
                                    appointment__id=appointment_id,
                                    appointment__user=request.user)

        appointment = invoice.appointment

        data = {
            "invoice_number": invoice.invoice_number,
            "appointment_id": appointment.id,

            "doctor": appointment.doctor.doctor.full_name,
            "patient": appointment.patient_name,
            "date": appointment.appointment_date,
            "time": appointment.appointment_time,

            "consultation_fee": float(invoice.consultation_fee),
            "gst_amount": float(invoice.gst_amount),
            "total_amount": float(invoice.total_amount),

            # PAYMENT DETAILS
            "payment_mode": appointment.payment_mode,
            "payment_bank": appointment.payment_bank,
            "payment_reference": appointment.payment_reference,
            "payment_transaction_id": appointment.payment_transaction_id,
            "payment_last4": appointment.payment_last4,

            "generated_at": invoice.generated_at,
        }

        return Response({"invoice": data})



class AppointmentInvoicePDFAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        invoice = get_object_or_404(
            AppointmentInvoice,
            appointment__id=appointment_id,
            appointment__user=request.user
        )

        appt = invoice.appointment

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)

        y = 800
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, f"Appointment Invoice #{invoice.invoice_number}")
        y -= 40

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"Appointment ID: {appt.id}")
        y -= 20
        pdf.drawString(50, y, f"Doctor: {appt.doctor.doctor.full_name}")
        y -= 20
        name =  appt.user.email
        pdf.drawString(50, y, f"Patient: {name}")

        y -= 20
        pdf.drawString(50, y, f"Date: {appt.appointment_date}")
        y -= 20
        pdf.drawString(50, y, f"Time: {appt.appointment_time}")
        y -= 40
        pdf.drawString(50, y, f"Consultation Fee: ₹{invoice.consultation_fee}")
        y -= 20
        pdf.drawString(50, y, f"GST (18%): ₹{invoice.gst_amount}")
        y -= 20

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, f"Total Amount: ₹{invoice.total_amount}")
        y -= 40

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"Payment Mode: {appt.payment_mode}")
        y -= 20
        pdf.drawString(50, y, f"Bank: {appt.payment_bank}")
        y -= 20
        pdf.drawString(50, y, f"Bank Reference No: {appt.payment_reference}")
        y -= 20
        pdf.drawString(50, y, f"Transaction ID: {appt.payment_transaction_id}")
        y -= 20
        pdf.drawString(50, y, f"Last 4 Digits: {appt.payment_last4}")
        y -= 40


        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"appointment_invoice_{invoice.invoice_number}.pdf"
        )
