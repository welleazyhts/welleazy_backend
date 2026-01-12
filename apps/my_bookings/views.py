from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from apps.common.utils.profile_helper import filter_by_effective_user
from rest_framework.views import APIView
from rest_framework import status as http_status
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework.parsers import MultiPartParser, FormParser
from apps.pharmacy.models import PharmacyOrder, PharmacyOrderItem, MedicineCoupon as PharmacyCoupon
from apps.labtest.models import Test as LabTestBooking
from apps.sponsored_packages.models import SponsoredPackage as SponsoredPackageBooking
from apps.health_packages.models import HealthPackage as HealthPackageBooking
from .serializers import PharmacyOrderItemSerializer
from io import BytesIO
from django.http import FileResponse
from apps.invoices.models import AppointmentInvoice
from apps.appointments.models import  MedicalReports

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import datetime 

import io



from apps.appointments.models import Appointment
# Status buckets
SCHEDULED = ['scheduled','pending', 'confirmed', 'booked', 'upcoming']
COMPLETED = ['completed', 'delivered', 'done']
CANCELLED = ['cancelled', 'order_cancelled', 'rejected']

SERVICE_MAP = {
    "appointment": "appointment",
    "pharmacy": "pharmacy",
    "pharmacy_coupon": "pharmacy_coupon",
    "labtest": "labtest",
    "sponsored_package": "sponsored_package",
    "health_package": "health_package",
}



class MyBookingsCleanAPIView(APIView):
  
    def get(self, request):
        user = request.user
        filter_status = request.GET.get('status', 'all')
        from_date = request.GET.get("from")
        to_date = request.GET.get("to")
        service = request.GET.get("service")   # appointment, pharmacy, labtest...
        # ignore type completely


        def match_status(s):
            if filter_status == 'all':
                return True
            if filter_status == 'scheduled':
                return s in SCHEDULED
            if filter_status == 'completed':
                return s in COMPLETED
            if filter_status == 'cancelled':
                return s in CANCELLED
            return True
        
       
        def match_date(date_value):
            
            if not date_value:
                return True
            # Normalize to datetime
            if isinstance(date_value, datetime.datetime):
                item_date = date_value.date()

            elif isinstance(date_value, datetime.date):
                item_date = date_value

            elif isinstance(date_value, str):
                try:
                    item_date = datetime.datetime.strptime(date_value, "%Y-%m-%d").date()
                except:
                    return True
            else:
                return True

            # FROM filter
            if from_date:
                try:
                    from_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
                    if item_date < from_dt:
                        return False
                except:
                    pass

            # TO filter
            if to_date:
                try:
                    to_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
                   
                    if item_date > to_dt:
                        return False
                except:
                    pass

            return True


        


        results = []

        # APPOINTMENTS
        appointments = Appointment.objects.filter(user=user).select_related("user")
        appointments = filter_by_effective_user(appointments, request)
        
        for a in appointments:
            if not match_status(a.status):
                continue

            if not a.scheduled_at:
                continue
            
            if not match_date(a.scheduled_at.date()):
                continue


            patient_name = (
                a.patient_name or 
                # request.user.get_username() or 
                a.user.email
            )

            results.append({
                'type': 'appointment',
                'appointment_id': a.id,
                'status': a.status,
                'patient_name': patient_name,
                'type_of_service': 'Consultation',
                'appointment_type': a.mode,
                'appointment_date': a.scheduled_at.date(),
                'appointment_time': a.scheduled_at.time(),

                'actions': {
                    'upload_health_records_url': f'/api/my-bookings/appointments/{a.id}/upload-report/',
                    'download_prescription_url': f'/api/my-bookings/appointments/{a.id}/prescription/',
                    'download_invoice_url': f'/api/appointments/{a.id}/invoice/pdf/',
                    'view_voucher_url': f'/api/my-bookings/appointments/{a.id}/voucher/',
                }
            })


        # PHARMACY ORDERS
        for p in PharmacyOrder.objects.filter(user=user).select_related("address"):
            if not match_status(p.status):
                continue
            if not match_date(p.ordered_date):
                continue

            
            # Serialize address safely
            address_data = None
            if p.address:
                address_data = {
                    "id": p.address.id,
                    "address": f"{p.address.address_line1}, {p.address.address_line2}",
                    "city": str(p.address.city),
                    "state": str(p.address.state),
                    "pincode": p.address.pincode,
                }

            results.append({
                'type': 'pharmacy',
                'order_id': p.order_id,
                'status': p.status,
                'patient_name': p.patient_name,
                'type_of_service': 'Pharmacy',
                'order_type': p.order_type,
                'ordered_date': p.ordered_date,
                'expected_delivery': p.expected_delivery_date,
                'order_amount': p.total_amount,
                'address': address_data,

                'actions': {
                    'view_medicine_details_url': f'/api/my-bookings/pharmacy/order/{p.id}/medicines/',
                    'view_voucher_url': f'/api/my-bookings/pharmacy/order/{p.id}/voucher/download/pdf/',
                }
            })


        # PHARMACY COUPONS
        for c in PharmacyCoupon.objects.filter(user=user).select_related("vendor"):
            if not match_status(c.status):
                continue
            
            if not match_date(c.created_at.date()):
                continue
            patient_name = (
                #c.user.get_name() or
                c.user.email
            )

            results.append({
                'type': 'pharmacy_coupon',
                'order_id': c.coupon_code,
                'status': c.status,
                'patient_name': patient_name,
                'type_of_service': 'Pharmacy Coupon',
                'coupon': c.coupon_name,
                'ordered_date': c.created_at,
                'vendor': c.vendor.name if c.vendor else None,

                'actions': {
                    'view_voucher_url': f'/api/my-bookings/pharmacy-coupon/{c.id}/voucher/'
                }
            })


        # LAB TEST BOOKINGS
        for l in LabTestBooking.objects.filter(user=user):
            if not match_status(l.status):
                continue
            if not match_date(l.created_at.date()):
                continue

            results.append({
                'type': 'labtest',
                'booking_id': l.id,
                'status': l.status,
                'patient_name': user.name ,#user.get_name() or user.email,
                'type_of_service': 'Lab Test',
                'booked_date': l.created_at.date(),

                'actions': {
                    'view_voucher_url': f'/api/my-bookings/labtest/{l.id}/voucher/'
                }
            })


        # SPONSORED PACKAGE BOOKINGS
        for s in SponsoredPackageBooking.objects.filter(user=user):
            if not match_status(s.status):
                continue
            if not match_date(s.created_at.date()):
                continue

            results.append({
                'type': 'sponsored_package',
                'booking_id': s.id,
                'package_name': s.name,
                'patient_name': user.name, #user.get_name() or user.email,
                'type_of_service': 'Sponsored Package',
                'status': s.status,

                'actions': {
                    'view_voucher_url': f'/api/my-bookings/sponsored-package/{s.id}/voucher/'
                }
            })


        # HEALTH PACKAGE BOOKINGS
        for h in HealthPackageBooking.objects.filter(user=user):
            if not match_status(h.status):
                continue
            
            if not match_date(h.created_at.date()):
                continue


            results.append({
                'type': 'health_package',
                'booking_id': h.id,
                'package_name': h.name,
                'patient_name': user.name, #user.get_name() or user.email,
                'type_of_service': 'Health Package',
                'status': h.status,

                'actions': {
                    'view_voucher_url': f'/api/my-bookings/health-package/{h.id}/voucher/'
                }
            })
# SORT FINAL LIST
        # Service filter (FINAL)

        if service:
            service=service.lower().strip()




        if service:
            results = [item for item in results if item.get("type") == service]


        def safe_date(value):
            
            if isinstance(value, datetime.datetime):
                return value.date()

            if isinstance(value, datetime.date):
                return value

            if isinstance(value, str):
                try:
                    return datetime.datetime.strptime(value, "%Y-%m-%d").date()
                except:
                    return datetime.date.min

            return datetime.date.min


        def sort_key(x):
            return safe_date(
                x.get("ordered_date")
                or x.get("booked_date")
                or x.get("obj.scheduled_at.date()")
            )

        results_sorted = sorted(results, key=sort_key, reverse=True)
        return Response(results_sorted)


# APPOINTMENT
# class AppointmentPrescriptionDownloadView(APIView):
#     def get(self, request, pk):
#         ap = get_object_or_404(DoctorPrescription, appointment__id=pk)
#         if not ap.prescription_file:
#             raise Http404('Prescription not available')
#         return FileResponse(ap.prescription_file.open('rb'), filename=f'appt_{ap.appointment_id}_prescription.pdf')


# class AppointmentInvoiceDownloadView(APIView):
#     def get(self, request, pk):
#         invoice = get_object_or_404(
#             AppointmentInvoice,
#             appointment__id=pk,
#             appointment__user=request.user
#         )

#         buffer = io.BytesIO()
#         p = canvas.Canvas(buffer)

#         p.drawString(100, 800, f"Invoice #{invoice.invoice_number}")
#         p.drawString(100, 780, f"Consultation Fee: {invoice.consultation_fee}")
#         p.drawString(100, 760, f"GST: {invoice.gst_amount}")
#         p.drawString(100, 740, f"Total: {invoice.total_amount}")
#         p.drawString(100, 720, f"Generated At: {invoice.generated_at}")

#         p.showPage()
#         p.save()
#         buffer.seek(0)

#         return FileResponse(buffer, as_attachment=True, filename=f"appointment_{pk}_invoice.pdf")


class MedicalReportUploadReportView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, id=pk, user=request.user)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "File is required"}, status=400)

        report = MedicalReports.objects.create(
            appointment=appt,
            user=request.user,
            file=uploaded_file
        )

        return Response({
            "message": "Health report uploaded",
            "report_id": report.id,
            "file_url": report.file.url,
            "uploaded_at": report.uploaded_at
        })


# PHARMACY ORDER


class PharmacyOrderMedicinesView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(PharmacyOrder, pk=pk, user=request.user)
        items = order.items.all()
        serializer = PharmacyOrderItemSerializer(items, many=True)
        return Response({'order_id': order.order_id, 'items': serializer.data})


class PharmacyOrderPrescriptionDownloadView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(PharmacyOrder, pk=pk, user=request.user)
        if not order.prescription_file:
            raise Http404('Prescription not available')
        return FileResponse(order.prescription_file.open('rb'), filename=f'pharmacy_{order.order_id}_prescription.pdf')

# class PharmacyOrderInvoiceDownloadView(APIView):
#     def get(self, request, pk):
#         order = get_object_or_404(PharmacyOrder, pk=pk, user=request.user)
#         if not order.invoice_file:
#             raise Http404('Invoice not available')
#         return FileResponse(order.invoice_file.open('rb'), filename=f'pharmacy_{order.order_id}_invoice.pdf')

# class GenericVoucherView(APIView):
#     def get(self, request, kind, pk):
#         model_map = {
#             'appointments': Appointment,
#             'pharmacy': PharmacyOrder,
#             'pharmacy-coupon': PharmacyCoupon,
#             'labtest': LabTestBooking,
#             'sponsored-package': SponsoredPackageBooking,
#             'health-package': HealthPackageBooking,
#         }
#         model = model_map.get(kind)
#         if not model:
#             return Response({'detail':'unknown kind'}, status=http_status.HTTP_400_BAD_REQUEST)
#         obj = get_object_or_404(model, pk=pk, user=request.user)
#         data = {
#             'id': getattr(obj, 'appointment_id', getattr(obj, 'order_id', getattr(obj, 'booking_id', getattr(obj , 'coupon_code', None)))),
#             'status': obj.status,
#             'type-of-service': kind,
#             'patient-name': request.user.get_username(),
#             'created_at': obj.created_at,
#             'vendor': getattr(obj,)
#         }
#         return Response({'voucher': data})


class AppointmentVoucherView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(Appointment, pk=pk, user=request.user)

        data = {
            "id": obj.id,
            "type": "appointment",
            "patient_name": obj.patient_name,
            "status": obj.status,
            "appointment_type": obj.mode,
            "appointment_date": obj.scheduled_at.date(),

            "appointment_time": obj.scheduled_at.time(),
            "booked_at": obj.created_at,
        }
        return Response({"voucher": data})


class PharmacyOrderVoucherView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(PharmacyOrder, pk=pk, user=request.user)

        # Order items
        items = PharmacyOrderItem.objects.filter(order=order)
        item_list = [
            {
                "sr_no": idx,
                "medicine_id": item.medicine.id,
                "medicine_name":item.medicine.name,
                "quantity": item.quantity,
                "net_amount": float(item.amount)
            }
            for idx, item in enumerate(items, start=1)
        ]

        data = {
            "order_id": order.order_id,
            "status": order.status,
            "patient_name": order.patient_name,
            "type_of_service": "Pharmacy",
            "order_type": order.order_type,
            "ordered_date": order.ordered_date.strftime("%d/%m/%Y"),
            "expected_delivery": order.expected_delivery_date.strftime("%d/%m/%Y"),
            "shipping_address": str(order.address) if order.address else None,

            "items": item_list,
            "payable_amount": float(order.total_amount),
        }

        return Response({"voucher": data})





class PharmacyOrderVoucherPDFSimpleView(APIView):

    def get(self, request, pk):
        order = get_object_or_404(PharmacyOrder, pk=pk, user=request.user)
        items = PharmacyOrderItem.objects.filter(order=order)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        x = 40
        y = 800

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(x, y, "Pharmacy Order Voucher")
        y -= 20
        pdf.setFont("Helvetica", 12)
        pdf.drawString(x, y, "-" * 50)
        y -= 30

        # Order info
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, y, f"Order ID: {order.order_id}")
        y -= 18
        pdf.drawString(x, y, f"Status: {order.status}")
        y -= 18
        pdf.drawString(x, y, f"Patient Name: {order.patient_name}")
        y -= 30

        # Service details
        pdf.drawString(x, y, f"Type of Service: Pharmacy")
        y -= 18
        pdf.drawString(x, y, f"Order Type: {order.order_type}")
        y -= 18
        pdf.drawString(x, y, f"Ordered Date: {order.ordered_date.strftime('%d/%m/%Y')}")
        y -= 18
        pdf.drawString(x, y, f"Expected Delivery: {order.expected_delivery_date.strftime('%d/%m/%Y')}")
        y -= 30

        # Address
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, y, "Shipping Address:")
        y -= 18
        pdf.setFont("Helvetica", 12)
        address_text = str(order.address)
        pdf.drawString(x, y, address_text)

        y -= 30

        # Items
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, y, "Items:")
        y -= 20
        pdf.setFont("Helvetica", 12)

        for idx, item in enumerate(items, start=1):
            pdf.drawString(x, y, f"{idx}. {item.medicine.name}  (Qty: {item.quantity})  - {item.amount}")
            y -= 18

        y -= 20

        # Total amount
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, y, f"Total Payable Amount: ₹{order.total_amount:.2f}")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"pharmacy_voucher_{order.order_id}.pdf"
        )



class PharmacyCouponVoucherView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(PharmacyCoupon, pk=pk, user=request.user)

        data = {
            "id": obj.coupon_code,
            "coupon_name":obj.coupon_name,
            "name":request.user.get_username(),
            "city":obj.city,
            "medicine_name":obj.medicine_name,
            "vendor":  obj.vendor.name if obj.vendor else None,
        }
        return Response({"voucher": data})


class LabTestVoucherView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(LabTestBooking, pk=pk)

        data = {
            "id": obj.id,
            "type": "labtest",
            "patient_name":request.user.get_username(),
            "status": "active" if str(obj.active).lower() == "true" else "inactive",
            "booked_date": obj.created_at.date(),
            "created_at": obj.created_at,
        }
        return Response({"voucher": data})


class SponsoredPackageVoucherView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(SponsoredPackageBooking, pk=pk)

        data = {
            "id": obj.id,
            "type": "sponsored_package",
            "package_name": obj.name,
            "patient_name": request.user.get_username(),
            "status": obj.status,
            "created_at": obj.created_at,
        }
        return Response({"voucher": data})


class HealthPackageVoucherView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(HealthPackageBooking, pk=pk)

        data = {
            "id": obj.id,
            "type": "health_package",
            "package_name": obj.name,
            "patient_name": request.user.get_username(),
            "status": obj.status,
            "created_at": obj.created_at,
        }
        return Response({"voucher": data})





