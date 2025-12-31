from .base import *
import environ
env = environ.Env()
environ.Env.read_env()      



DEBUG = True

ALLOWED_HOSTS = ["*"]

# SQLite for development (easy setup, no external DB needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL (uncomment for production)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv("DB_NAME"),
#         'USER': os.getenv("DB_USER"),
#         'PASSWORD': os.getenv("DB_PASSWORD"),
#         'HOST': os.getenv("DB_HOST"),
#         'PORT': os.getenv("DB_PORT"),
#         'CONN_MAX_AGE': 60,
#     }
# }
# EMAIL SETTINGS
# Use console backend for development (emails print to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Uncomment below for real email sending via Gmail SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = env("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="test@example.com")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Celery Configuration Options
import os
from dotenv import load_dotenv
from celery.schedules import crontab
load_dotenv()

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_ENABLE_UTC = False

CELERY_BEAT_SCHEDULE = {
    "send_appointment_reminders_every_5_minutes": {
        "task": "apps.notifications.tasks.send_upcoming_appointment_reminders",
        "schedule": 5 * 60,  # every 5 minute
    },
    #  "send-upcoming-care-program-reminders": {
    #     "task": "apps.notifications.tasks.send_upcoming_care_program_reminders",
    #     "schedule": 5 * 60,
    # },
    "send-upcoming-pharmacy-delivery-reminders": {
        "task": "apps.notifications.tasks.send_upcoming_pharmacy_delivery_reminders",
        "schedule": 5 * 60,
    },
}



# Default from email (uses console backend in dev) 
# client API settings for development
CLIENT_CITY_API_URL = None
CLIENT_TEST_API_URL = None
CLIENT_DIAGNOSTIC_API_URL = None
CLIENT_VISIT_TYPE_API_URL = None
CLIENT_HEALTH_PACKAGE_API_URL = None
CLIENT_SPONSORED_PACKAGE_API_URL = None

CLIENT_DOCTORSPECIALITY_API_URL=None
CLIENT_LANGUAGE_API_URL=None
CLIENT_PINCODE_API_URL=None
CLIENT_DOCTOR_URL=None
CLIENT_VENDOR_URL=None

