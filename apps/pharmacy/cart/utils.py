import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.core.cache import cache
from django.conf import settings

PINCODE_CACHE_KEY = "client_pincodes_zones"
PINCODE_CACHE_TIMEOUT = 86400  # 24 hours


def get_pincode_zone(pincode):
    # Fetch pincode zone info from client API once per day.

    zone_data = cache.get(PINCODE_CACHE_KEY)

    # If not in cache → fetch from client API
    if not zone_data:
        try:
            url = settings.CLIENT_PINCODE_URL
            res = requests.get(url, timeout=5)

            if res.status_code == 200:
                zone_data = res.json()         # [{pincode, zone}, ...]
                cache.set(PINCODE_CACHE_KEY, zone_data, PINCODE_CACHE_TIMEOUT)
            else:
                zone_data = []
        except:
            zone_data = []

    # Find the pincode in dataset
    for item in zone_data:
        if str(item["pincode"]) == str(pincode):
            return item.get("zone")

    return None   # Not found


def estimate_delivery_date(pincode, order_datetime=None):
    # Delivery estimation based on dynamic pincode zone from client.

    from django.conf import settings

    if not order_datetime:
        order_datetime = datetime.now(ZoneInfo("Asia/Kolkata"))

    zone = get_pincode_zone(pincode)

    # Default days if zone unknown
    days = 5

    if zone == "metro":
        days = 2
    elif zone == "tier1":
        days = 3
    elif zone == "tier2":
        days = 4
    elif zone == "remote":
        days = 7

    # Cutoff dependency (same logic)
    if order_datetime.hour >= 18:
        days += 1

    estimated = order_datetime + timedelta(days=days)

    # Move from Sunday → Monday
    if estimated.weekday() == 6:
        estimated += timedelta(days=1)

    return estimated.date()
