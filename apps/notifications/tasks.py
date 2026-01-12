from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Notification
from django.utils import timezone
from datetime import timedelta
from apps.appointments.models import Appointment

# from apps.care_programs.models import CareProgramBooking
from apps.pharmacy.models import PharmacyOrder


User = get_user_model()   # <-- CRITICAL FIX

@shared_task
def create_scheduled_notification(user_id, title, message):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False  # user not found

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        created_at=timezone.now()
    )
    return "OK"


# APPOINTMENT REMINDERS TASK
@shared_task
def send_upcoming_appointment_reminders():

    now = timezone.now()
    # window: next 12 hours
    window_start = now
    window_end = now + timedelta(hours=12)

    appointments = Appointment.objects.filter(
        scheduled_at__isnull=False,
        status__iexact="confirmed",
        reminder_sent=False,
        scheduled_at__gt=window_start,
        scheduled_at__lte=window_end,
    )

    for appt in appointments:
        user = appt.user
        when = timezone.localtime(appt.scheduled_at)
        when.strftime(' %I:%M %p')
       
        title = "Appointment Reminder"
        message = (
            f"You have an upcoming {appt.item_type.replace('_', ' ')} scheduled for "
            f"{when.strftime('%d %b %Y')} at {when.strftime('%I:%M %p')}."
        )

        # fire async notification task
        create_scheduled_notification.delay(user.id, title, message)

        # mark reminder as sent
        appt.reminder_sent = True
        appt.save(update_fields=["reminder_sent"])


# CARE PROGRAM REMINDERS TASK

# @shared_task
# def send_upcoming_care_program_reminders():
#     now = timezone.now()
#     window_start = now
#     window_end = now + timedelta(hours=12)

#     enrollments = CareProgramBooking.objects.filter(
#         next_session_at__isnull=False,
#         status__iexact="active",
#         reminder_sent=False,
#         next_session_at__gt=window_start,
#         next_session_at__lte=window_end,
#     )

#     for cp in enrollments:
#         user = cp.user
#         when = timezone.localtime(cp.next_session_at)

#         title = "Care Program Reminder"
#         message = (
#             f"You have an upcoming care program session for "
#             f"{getattr(cp, 'program_name', 'your care plan')} on "
#             f"{when.strftime('%d %b %Y')} at {when.strftime('%I:%M %p')}."
#         )

#         create_scheduled_notification.delay(user.id, title, message)
#         cp.reminder_sent = True
#         cp.save(update_fields=["reminder_sent"])


# PHARMACY DELIVERY REMINDERS TASK

@shared_task
def send_upcoming_pharmacy_delivery_reminders():
    now = timezone.now()
    window_start = now
    window_end = now + timedelta(hours=12)

    orders = PharmacyOrder.objects.filter(
        expected_delivery_date__isnull=False,
        status__in=["shipped", "out_for_delivery"],
        reminder_sent=False,
        expected_delivery_date__gt=window_start,
        expected_delivery_date__lte=window_end,
        status="booked",
    )

    for order in orders:
        user = order.user
        when = timezone.localtime(order.expected_delivery)

        title = "Pharmacy Delivery Reminder"
        message = (
            f"Your pharmacy order #{order.id} is scheduled for delivery on "
            f"{when.strftime('%d %b %Y')} at {when.strftime('%I:%M %p')}."
        )

        create_scheduled_notification.delay(user.id, title, message)
        order.reminder_sent = True
        order.save(update_fields=["reminder_sent"])