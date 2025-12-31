import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = False  # overridden in development.py

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    
    'apps.accounts',
    'apps.location',
    'apps.contact',
    'apps.partner',
    'apps.consultation_filter',
    'apps.labtest',
    'apps.diagnostic_center',
    'apps.labfilter',
    'apps.dependants',
    # 'apps.addresses',
    'apps.addresses.apps.AddressesConfig',

    # 'apps.doctor_details',
    'apps.doctor_details.apps.DoctorDetailsConfig',


    'apps.appointments',
    'apps.health_packages',
    'apps.sponsored_packages',

    'apps.health_records.health',
    'apps.pharmacy',
    'apps.pharmacy.cart',
    'apps.health_records.prescriptions',
    'apps.health_records.hospitalizations',
    'apps.health_records.medical_bills',
    'apps.health_records.vaccination_certificates',
    'apps.health_records.medicine_reminders',
    'apps.health_records.common',
    
    'apps.insurance_records',
    'apps.care_programs',
    
    'apps.health_assessment',
    
    'apps.my_bookings',
    'apps.invoices',
    'apps.gym_service',
    # 'apps.eyedental_care',
    'apps.eyedental_care.apps.EyedentalCareConfig',
    'apps.feedback',
    'apps.women_health',
    'apps.payments',
    'apps.notifications',

    # Case Management & CRM
    'apps.common',
    'apps.cases',
    'apps.corporates',

    # Healthcare Service Providers Integration
    'apps.providers',

     # Third-party apps
    'rest_framework',
    "channels",
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist'
]

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },

    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'INFO',
        },

        # Enable logs for your app
        'apps.health_records': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    "apps.common.middleware.current_user.CurrentUserMiddleware",
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'welleazy_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI_APPLICATION = 'welleazy_backend.wsgi.application'

# Database (configured in development/production)
DATABASES = {}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000")

#Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

#Fast2SMS
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")
FAST2SMS_SENDER_ID = os.getenv("FAST2SMS_SENDER_ID")
FAST2SMS_ROUTE = os.getenv("FAST2SMS_ROUTE")
FAST2SMS_LANGUAGE = os.getenv("FAST2SMS_LANGUAGE")

#Razorpay
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

ASGI_APPLICATION = "welleazy_backend.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    },
}

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'



# Client API Settings
CLIENT_API_TOKEN = os.getenv("CLIENT_API_TOKEN", None)

CLIENT_CITY_API_URL = os.getenv("CLIENT_CITY_API_URL", None)
CLIENT_TEST_API_URL = os.getenv("CLIENT_TEST_API_URL", None)
CLIENT_DIAGNOSTIC_API_URL = os.getenv("CLIENT_DIAGNOSTIC_API_URL", None)
CLIENT_VISIT_TYPE_API_URL = os.getenv("CLIENT_VISIT_TYPE_API_URL", None)
CLIENT_HEALTH_PACKAGE_API_URL = os.getenv("CLIENT_HEALTH_PACKAGE_API_URL", None)
CLIENT_SPONSORED_PACKAGE_API_URL = os.getenv("CLIENT_SPONSORED_PACKAGE_API_URL", None)



CLIENT_DOCTORSPECIALITY_API_URL=os.getenv("CLIENT_DOCTORSPECIALITY_API_URL",None)
CLIENT_LANGUAGE_API_URL=os.getenv("CLIENT_LANGUAGE_API_URL",None)
CLIENT_PINCODE_API_URL=os.getenv("CLIENT_PINCODE_API_URL",None)
CLIENT_DOCTOR_URL=os.getenv("CLIENT_DOCTOR_URL",None)
CLIENT_VENDOR_URL=os.getenv("CLIENT_VENDOR_URL",None)

# Tata 1MG Partner API Settings
ONEMG_API_BASE_URL = os.getenv("ONEMG_API_BASE_URL", "https://api.1mg.com")
ONEMG_CLIENT_ID = os.getenv("ONEMG_CLIENT_ID", "")
ONEMG_CLIENT_SECRET = os.getenv("ONEMG_CLIENT_SECRET", "")
ONEMG_MERCHANT_ID = os.getenv("ONEMG_MERCHANT_ID", "")
ONEMG_WEBHOOK_SECRET = os.getenv("ONEMG_WEBHOOK_SECRET", "")
ONEMG_API_TIMEOUT = int(os.getenv("ONEMG_API_TIMEOUT", "30"))

# Apollo Partner API Settings
APOLLO_API_BASE_URL = os.getenv("APOLLO_API_BASE_URL", "https://api.apollo247.com")
APOLLO_USERNAME = os.getenv("APOLLO_USERNAME", "")
APOLLO_PASSWORD = os.getenv("APOLLO_PASSWORD", "")
APOLLO_CLIENT_ID = os.getenv("APOLLO_CLIENT_ID", "")
APOLLO_AGREEMENT_ID = os.getenv("APOLLO_AGREEMENT_ID", "")
APOLLO_API_TIMEOUT = int(os.getenv("APOLLO_API_TIMEOUT", "30"))

# Default Healthcare Service Providers
DEFAULT_CONSULTATION_PROVIDER = os.getenv("DEFAULT_CONSULTATION_PROVIDER", "apollo")
DEFAULT_DIAGNOSTICS_PROVIDER = os.getenv("DEFAULT_DIAGNOSTICS_PROVIDER", "apollo")
DEFAULT_PHARMACY_PROVIDER = os.getenv("DEFAULT_PHARMACY_PROVIDER", "onemg")

