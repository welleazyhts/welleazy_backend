from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Count
from .models import CartItem, DiagnosticCenter

def generate_time_slots_for_center(center: DiagnosticCenter, date_obj):
    # Returns list of slot time objects for the given date based on center work_start/work_end and interval.
    start = center.work_start or time(8, 0)
    end = center.work_end or time(18, 0)
    interval = center.slot_interval_minutes or 30

    slots = []
    # build datetime objects anchored on date_obj
    current = datetime.combine(date_obj, start)
    end_dt = datetime.combine(date_obj, end)

    while current <= end_dt - timedelta(minutes=interval):
        slot_start = current.time()
        slot_end_dt = current + timedelta(minutes=interval)
        slots.append({
            "start_time": slot_start, 
            "end_time": slot_end_dt.time()
        })
        current = slot_end_dt

    return slots

def get_slot_booked_count(center_id, date_obj, slot_time):
    # Count confirmed bookins (CartItems with item_type='test' and slot_confirmed True)
    # matching the exact slot_time for that diagnostic center and date.
    return CartItem.objects.filter(
        item_type="test",
        diagnostic_center_id=center_id,
        selected_date=date_obj,
        selected_time=slot_time,
        slot_confirmed=True
    ).count()
