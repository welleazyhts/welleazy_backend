import logging
from django.db.models import Q

# Import models
from apps.accounts.models import UserProfile
from apps.appointments.models import Appointment
from apps.health_records.health.models import (
    HeightRecord, WeightRecord, BmiRecord, BloodPressureRecord, 
    HeartRateRecord, OxygenSaturationRecord, GlucoseRecord
)
from apps.health_records.prescriptions.models import PrescriptionRecord
from apps.health_records.medical_bills.models import MedicalBillRecord
from apps.health_records.hospitalizations.models import HospitalizationRecord
from apps.health_records.medicine_reminders.models import MedicineReminder
from apps.health_records.vaccination_certificates.models import VaccinationCertificateRecord
from apps.insurance_records.models import InsurancePolicyRecord
from apps.labtest.models import Test
from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage
from apps.diagnostic_center.models import DiagnosticCenter
from apps.pharmacy.models import Medicine, PharmacyOrder
from apps.pharmacy.cart.models import Cart
from apps.care_programs.models import CareProgramBooking
from apps.health_assessment.models import HealthAssessment
from apps.doctor_details.models import DoctorProfessionalDetails
from apps.consultation_filter.models import DoctorSpeciality
from apps.gym_service.models import GymPackage, Voucher
from apps.eyedental_care.models import EyeDentalCareBooking
from apps.women_health.models import CycleEntry
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)

class ChatbotTools:
    def __init__(self, user=None):
        self.user = user

    def get_user_profile(self):
        # Get user profile and linked family members
        if not self.user: return "User not authenticated."
        
        dependants = self.user.dependants.all()
        dependant_list = [
            {
                "name": d.name,
                "member_id": d.member_id,
                "relationship": d.relationship.name if d.relationship else "Other",
                "gender": d.gender
            } for d in dependants
        ]

        try:
            profile = UserProfile.objects.get(user=self.user)
            return {
                "name": self.user.name,
                "email": self.user.email,
                "mobile": self.user.mobile_number,
                "member_id": self.user.member_id,
                "employee_id": self.user.employee_id,
                "gender": profile.gender,
                "dob": str(profile.dob),
                "blood_group": profile.blood_group,
                "corporate_name": profile.corporate_name,
                "dependants": dependant_list
            }
        except UserProfile.DoesNotExist:
            return {
                "name": self.user.name,
                "email": self.user.email,
                "mobile": self.user.mobile_number,
                "member_id": self.user.member_id,
                "dependants": dependant_list
            }

    def get_user_appointments(self):
        # Fetch recent and upcoming appointments
        if not self.user: return "User not authenticated."
        appointments = Appointment.objects.filter(user=self.user).select_related(
            'doctor__doctor', 'diagnostic_center'
        ).order_by('-scheduled_at')[:5]
        results = []
        for app in appointments:
            patient_name = app.patient_name
            if not patient_name:
                if app.for_whom == "dependant" and app.dependant:
                    patient_name = app.dependant.name
                else:
                    patient_name = self.user.name if hasattr(self.user, 'name') else str(self.user)

            results.append({
                "appointment_id": app.id,
                "service_type": app.item_type,
                "status": app.status,
                "beneficiary": app.for_whom,
                "patient_name": patient_name,
                "scheduled_at": app.scheduled_at.strftime("%Y-%m-%d %H:%M") if app.scheduled_at else "Not yet scheduled",
                "doctor": app.doctor.doctor.full_name if (app.doctor and app.doctor.doctor) else None,
                "diagnostic_center": app.diagnostic_center.name if app.diagnostic_center else None
            })
        return results if results else "No appointments found."

    def get_user_health_vitals(self):
        # Get latest health metrics (BP, Weight, etc.)
        if not self.user: return "User not authenticated."
        vitals = {}
        
        latest_bp = BloodPressureRecord.objects.filter(user=self.user).first()
        if latest_bp: vitals["blood_pressure"] = f"{latest_bp.systolic}/{latest_bp.diastolic} {latest_bp.unit}"
        
        latest_weight = WeightRecord.objects.filter(user=self.user).first()
        if latest_weight: vitals["weight"] = f"{latest_weight.value} {latest_weight.unit}"

        latest_height = HeightRecord.objects.filter(user=self.user).first()
        if latest_height: vitals["height"] = f"{latest_height.value} {latest_height.unit}"
        
        latest_hr = HeartRateRecord.objects.filter(user=self.user).first()
        if latest_hr: vitals["heart_rate"] = f"{latest_hr.value} {latest_hr.unit}"

        latest_spo2 = OxygenSaturationRecord.objects.filter(user=self.user).first()
        if latest_spo2: vitals["spo2"] = f"{latest_spo2.value}{latest_spo2.unit}"
        
        latest_glucose = GlucoseRecord.objects.filter(user=self.user).first()
        if latest_glucose: vitals["glucose"] = f"{latest_glucose.value} {latest_glucose.unit} ({latest_glucose.test_type})"
        
        return vitals if vitals else "No health vitals found."

    def get_user_medical_documents(self):
        # List medical records and reports
        if not self.user: return "User not authenticated."
        records = PrescriptionRecord.objects.filter(user=self.user).prefetch_related('parameters').order_by('-record_date')[:5]
        results = []
        for r in records:
            parameters = [
                f"{p.parameter_name}: {p.result} {p.unit}" 
                for p in r.parameters.all()
            ]
            results.append({
                "name": r.record_name,
                "type": r.record_type,
                "date": str(r.record_date),
                "patient": r.dependant.name if (r.for_whom == 'dependant' and r.dependant) else self.user.name,
                "doctor": r.doctor_name,
                "results": parameters
            })
        return results if results else "No medical documents found."

    def get_user_medicine_reminders(self):
        # Get active pill reminders and stock status
        if not self.user: return "User not authenticated."
        reminders = MedicineReminder.objects.filter(user=self.user)
        results = []
        for rem in reminders:
            times = [f"{t.time} ({t.meal_relation})" for t in rem.schedule_times.all()]
            results.append({
                "medicine": rem.medicine_name,
                "type": rem.medicine_type,
                "dosage": f"{rem.dosage_value} {rem.dosage_unit}",
                "schedule": times,
                "duration": f"{rem.duration_value} {rem.duration_unit}",
                "remaining_stock": rem.medicines_left,
                "doctor": rem.doctor_name
            })
        return results if results else "No medicine reminders found."

    def get_user_medical_history(self):
        # Hospitalization and vaccination history
        if not self.user: return "User not authenticated."
        hospitals = HospitalizationRecord.objects.filter(user=self.user).select_related('dependant').order_by('-admitted_date')[:5]
        vaccines = VaccinationCertificateRecord.objects.filter(user=self.user).select_related('dependant').order_by('-vaccination_date')[:5]
        
        def resolve_patient(record):
            if hasattr(record, 'patient_name') and record.patient_name:
                return record.patient_name
            if hasattr(record, 'dependant') and record.dependant:
                return record.dependant.name
            return self.user.name if hasattr(self.user, 'name') else str(self.user)

        history = {
            "hospitalizations": [
                {
                    "patient_name": resolve_patient(h),
                    "name": h.record_name,
                    "type": h.hospitalization_type,
                    "hospital": h.hospital_name,
                    "admitted": str(h.admitted_date),
                    "discharged": str(h.discharged_date) if h.discharged_date else "Present",
                    "doctor": h.doctor_name
                } for h in hospitals
            ],
            "vaccinations": [
                {
                    "patient_name": resolve_patient(v),
                    "vaccine": v.vaccination_name,
                    "dose": v.vaccination_dose,
                    "date": str(v.vaccination_date),
                    "center": v.vaccination_center
                } for v in vaccines
            ]
        }
        return history

    def get_user_medical_bills(self):
        # Fetch recent medical bills
        if not self.user: return "User not authenticated."
        bills = MedicalBillRecord.objects.filter(user=self.user).select_related('dependant').order_by('-record_date')[:5]
        
        def resolve_patient(record):
            if hasattr(record, 'patient_name') and record.patient_name:
                return record.patient_name
            if hasattr(record, 'dependant') and record.dependant:
                return record.dependant.name
            return self.user.name if hasattr(self.user, 'name') else str(self.user)

        return [
            {
                "patient_name": resolve_patient(r),
                "name": r.record_name,
                "type": r.bill_type,
                "date": str(r.record_date),
                "bill_number": r.record_bill_number,
                "hospital": r.record_hospital_name
            } for r in bills
        ]

    def get_user_insurance_policies(self):
        # Active insurance policies and coverage
        if not self.user: return "User not authenticated."
        policies = InsurancePolicyRecord.objects.filter(user=self.user).prefetch_related('floater_members__dependant')
        results = []
        for p in policies:
            members = [
                {
                    "name": m.dependant.name if m.dependant else self.user.name,
                    "uhid": m.uhid,
                    "is_self": m.is_self
                } for m in p.floater_members.all()
            ]
            results.append({
                "company": p.insurance_company,
                "policy_number": p.policy_number,
                "policy_name": p.policy_name,
                "type": p.type_of_insurance,
                "holder": p.policy_holder_name,
                "valid_from": str(p.policy_from),
                "valid_till": str(p.policy_to),
                "sum_assured": str(p.sum_assured),
                "premium": str(p.premium_amount),
                "plan_type": p.plan_type,
                "tpa": p.tpa,
                "nominee": p.nominee,
                "members": members if members else "Individual policy"
            })
        return results if results else "No insurance policies found."

    def search_lab_services(self, query: str):
        # Search lab tests, packages and centers
        if not query: return "Please provide a search query."
        words = [w.lower().rstrip('s') for w in query.split() if len(w) > 1]
        if not words: return "Search query too short."

        category_keywords = ["health", "package", "test", "lab", "center", "clinic", "diagnostic", "checkup", "check-up", "service"]
        is_category_search = any(any(w in kw or kw.startswith(w) for kw in category_keywords) for w in words)

        test_filter, package_filter, sponsored_filter, center_filter = [Q(active=True) for _ in range(4)]
        if not is_category_search:
            q_test = Q()
            q_center = Q()
            for w in words:
                q_test |= Q(name__icontains=w) | Q(code__icontains=w)
                q_center |= Q(name__icontains=w) | Q(area__icontains=w) | Q(city__name__icontains=w)
            test_filter &= q_test
            package_filter &= q_test
            sponsored_filter &= q_test
            center_filter &= q_center

        tests = Test.objects.filter(test_filter)[:5]
        packages = HealthPackage.objects.filter(package_filter)[:5]
        sponsored = SponsoredPackage.objects.filter(sponsored_filter)[:5]
        centers = DiagnosticCenter.objects.filter(center_filter).select_related('city')[:5]
        
        results = {}
        if tests: results["tests"] = [{"name": t.name, "code": t.code, "price": str(t.price)} for t in tests]
        if packages: results["health_packages"] = [{"name": p.name, "code": p.code, "price": str(p.price)} for p in packages]
        if sponsored: results["sponsored_packages"] = [{"name": p.name, "code": p.code, "price": str(p.price)} for p in sponsored]
        if centers: results["diagnostic_centers"] = [{"name": c.name, "city": c.city.name if c.city else "Unknown", "area": c.area, "contact": c.contact_number} for c in centers]
        return results if results else f"No lab services found matching your query. Try searching with one simple keyword (e.g. 'blood', 'sugar', 'Chennai')."

    def search_medicines(self, query: str):
        # Search available medicines
        if not query: return "Please provide a medicine name to search."
        words = [w.lower().rstrip('s') for w in query.split() if len(w) > 1]
        if not words: return "Search query too short."

        med_keywords = ["medicine", "med", "drug", "pharmacy", "pill", "tablet", "capsule", "syrup"]
        is_category_search = any(any(w in kw or kw.startswith(w) for kw in med_keywords) for w in words)

        med_filter = Q(deleted_at__isnull=True)
        if not is_category_search:
            q_med = Q()
            for w in words:
                q_med |= Q(name__icontains=w) | Q(category__name__icontains=w)
            med_filter &= q_med
        
        medicines = Medicine.objects.filter(med_filter)[:5]
        results = []
        for med in medicines:
            results.append({
                "name": med.name,
                "price": f"₹{med.selling_price}",
                "stock": "In Stock" if med.stock_count > 0 else "Out of Stock",
                "category": med.category.name if med.category else "General",
                "details": {"uses": med.details.uses if hasattr(med, 'details') else "Consult doctor", "side_effects": med.details.side_effects if hasattr(med, 'details') else "Not listed"}
            })
        return results if results else f"No medicines found matching your query. Try searching with just the medicine name."

    def get_pharmacy_cart(self):
        # Get pharmacy cart and cost breakdown
        if not self.user: return "User not authenticated."
        try:
            cart = Cart.objects.prefetch_related('items__medicine', 'address').get(user=self.user)
            items = []
            for item in cart.items.all():
                items.append({
                    "medicine": item.medicine.name,
                    "quantity": item.quantity,
                    "price_per_unit": str(item.medicine.selling_price),
                    "subtotal": str(item.medicine.selling_price * item.quantity)
                })
            
            if not items: return "Your pharmacy cart is empty."
            
            return {
                "items": items,
                "summary": {
                    "total_mrp": str(cart.total_mrp),
                    "total_selling_price": str(cart.total_selling),
                    "discount": str(cart.discount_on_mrp),
                    "delivery_charge": str(cart.delivery_charge),
                    "handling_fee": str(cart.handling_fee),
                    "platform_fee": str(cart.platform_fee),
                    "coupon_discount": str(cart.coupon_discount),
                    "total_payable": str(cart.total_pay)
                },
                "delivery_mode": cart.delivery_mode,
                "address": cart.address.address_line1 if cart.address else "Not set"
            }
        except Cart.DoesNotExist:
            return "You don't have a pharmacy cart yet."

    def get_pharmacy_order_history(self):
        # Pharmacy order history
        if not self.user: return "User not authenticated."
        orders = PharmacyOrder.objects.filter(user=self.user).prefetch_related('items__medicine').order_by('-created_at')[:5]
        results = []
        for order in orders:
            items = [f"{item.medicine.name} (x{item.quantity})" for item in order.items.all()]
            results.append({
                "order_id": order.order_id,
                "status": order.status,
                "date": str(order.ordered_date),
                "delivery_date": str(order.expected_delivery_date) if order.expected_delivery_date else "TBD",
                "total": str(order.total_amount),
                "items": items,
                "patient": order.patient_name
            })
        return results if results else "No pharmacy orders found."

    def get_user_care_program_bookings(self):
        # Care program bookings (elderly care, nursing, etc.)
        if not self.user: return "User not authenticated."
        bookings = CareProgramBooking.objects.filter(user=self.user).order_by('-created_at')[:5]
        results = []
        for b in bookings:
            results.append({
                "service": b.get_service_type_display(),
                "patient": b.name,
                "status": b.status,
                "date": b.created_at.strftime("%Y-%m-%d"),
                "requirements": b.requirements
            })
        return results if results else "No care program bookings found."

    def get_user_health_assessment(self):
        # Latest health assessment (HRA) results
        if not self.user: return "User not authenticated."
        assessment = HealthAssessment.objects.filter(user=self.user, status="active").order_by('-created_at').first()
        if not assessment: return "No active health assessments found."
        return {
            "risk_category": assessment.risk_category.upper() if assessment.risk_category else "LOW",
            "score": assessment.total_score,
            "date": assessment.created_at.strftime("%Y-%m-%d"),
            "health_opinion": assessment.health_opinion,
            "bmi": assessment.bmi
        }

    def search_doctors(self, query: str = None, city: str = None):
        # Search doctors by specialty, city or name
        q = Q()
        if query:
            q |= Q(doctor__full_name__icontains=query) | Q(specialization__name__icontains=query)
        if city:
            q &= Q(doctor__city__name__icontains=city)
        
        doctors = DoctorProfessionalDetails.objects.filter(q).select_related('doctor', 'doctor__city').prefetch_related('specialization')[:5]
        results = []
        for d in doctors:
            results.append({
                "name": d.doctor.full_name,
                "specialties": [s.name for s in d.specialization.all()],
                "experience": f"{d.experience_years} years",
                "fee": f"₹{d.consultation_fee}",
                "city": d.doctor.city.name if d.doctor.city else "N/A",
                "clinic": d.clinic_address
            })
        return results if results else "No doctors found matching your search."

    def get_user_gym_vouchers(self):
        # Active gym vouchers and status
        if not self.user: return "User not authenticated."
        vouchers = Voucher.objects.filter(user=self.user).order_by('-created_at')[:5]
        results = []
        for v in vouchers:
            results.append({
                "gym": v.gym_center.name,
                "package": v.package.title,
                "status": v.status,
                "purchased_on": v.created_at.strftime("%Y-%m-%d"),
                "city": v.city
            })
        return results if results else "No gym vouchers found."

    def search_gym_packages(self, query: str = None):
        # Search gym packages
        q = Q()
        if query:
            q = Q(title__icontains=query)
        packages = GymPackage.objects.filter(q)[:5]
        results = []
        for p in packages:
            results.append({
                "title": p.title,
                "duration": f"{p.duration_months} months",
                "price": f"₹{p.discounted_price}",
                "mrp": f"₹{p.original_price}"
            })
        return results if results else "No gym packages found."

    def get_user_eye_dental_bookings(self):
        # Eye and dental care bookings
        if not self.user: return "User not authenticated."
        bookings = EyeDentalCareBooking.objects.filter(user=self.user).order_by('-created_at')[:5]
        results = []
        for b in bookings:
            results.append({
                "type": b.get_care_program_type_display(),
                "service": b.get_service_type_display(),
                "patient": b.name,
                "status": b.status,
                "treatment": b.eye_treatment.name if b.eye_treatment else (b.dental_treatment.name if b.dental_treatment else "Routine Checkup")
            })
        return results if results else "No Eye or Dental bookings found."

    def get_woman_cycle_prediction(self):
        # Period and ovulation cycle predictions
        entry = CycleEntry.objects.order_by('-created_at').first()
        if not entry: return "No cycle data available."
        return {
            "last_period": str(entry.last_period_start),
            "next_period_start": str(entry.next_period_start),
            "ovulation_date": str(entry.ovulation_date),
            "fertile_window": f"{entry.fertile_window_start} to {entry.fertile_window_end}"
        }

    def get_user_notifications(self):
        # Recent alerts and notifications
        if not self.user: return "User not authenticated."
        notifications = Notification.objects.filter(user=self.user).order_by('-created_at')[:5]
        results = []
        for n in notifications:
            results.append({
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "time": n.created_at.strftime("%Y-%m-%d %H:%M")
            })
        return results if results else "No notifications found."

    def get_available_care_programs(self):
        # List all available care program categories
        return [
            {"service_id": choice[0], "service_name": choice[1]}
            for choice in CareProgramBooking.SERVICE_TYPE_CHOICES
        ]

    def get_doctor_specialties(self):
        # List all medical specialties available
        specialties = DoctorSpeciality.objects.filter(active=True).values_list('name', flat=True)
        return list(specialties) if specialties else "No specialties found."
