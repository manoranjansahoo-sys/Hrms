
"""
Django settings for company_hrms project.
Enterprise Human Resource Management System.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# =====================================================
# BASE DIRECTORY
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# =====================================================
# SECURITY SETTINGS
# =====================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY is missing from .env file")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]

# =====================================================
# CUSTOM USER MODEL
# =====================================================

AUTH_USER_MODEL = "accounts.CustomUser"

# =====================================================
# APPLICATION DEFINITION
# =====================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-Party Apps
    "rest_framework",

    # HRMS Modular Apps
    "accounts.apps.AccountsConfig",
    "organization.apps.OrganizationConfig",
    "employees.apps.EmployeesConfig",
    "attendance.apps.AttendanceConfig",
    "leave_management.apps.LeaveManagementConfig",
    "payroll.apps.PayrollConfig",
    "performance.apps.PerformanceConfig",
    "support.apps.SupportConfig",
    "notifications.apps.NotificationsConfig",
    "portal.apps.PortalConfig",
    "recruitment.apps.RecruitmentConfig",
]

# =====================================================
# EMAIL CONFIGURATION
# =====================================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Company HRMS Careers <careers@company.com>"
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

# =====================================================
# MIDDLEWARE
# =====================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =====================================================
# URL CONFIGURATION
# =====================================================

ROOT_URLCONF = "company_hrms.urls"

# =====================================================
# TEMPLATES
# =====================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "portal.context_processors.hrms_global_context",
            ],
        },
    },
]

WSGI_APPLICATION = "company_hrms.wsgi.application"

# =====================================================
# DATABASE CONFIGURATION - MYSQL
# =====================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "hrms_db"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}

# =====================================================
# PASSWORD VALIDATION
# =====================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =====================================================
# INTERNATIONALIZATION
# =====================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

# =====================================================
# STATIC FILES
# =====================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# =====================================================
# MEDIA FILES
# =====================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# =====================================================
# DEFAULT PRIMARY KEY
# =====================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================
# AUTHENTICATION URLS
# =====================================================

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "portal:home"

LOGOUT_REDIRECT_URL = "accounts:login"

# =====================================================
# DJANGO MESSAGES
# =====================================================

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# =====================================================
# SESSION AND COOKIE SECURITY
# =====================================================

SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_HTTPONLY = False

SESSION_COOKIE_AGE = 86400  # 24 hours

# =====================================================
# GOOGLE OAUTH CONFIGURATION
# =====================================================

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv(
    "GOOGLE_CLIENT_ID", ""
)

SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET", ""
)

# =====================================================
# PRODUCTION SECURITY
# =====================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
CSRF_TRUSTED_ORIGINS = [
    "https://designlope.in",
    "https://accounts.google.com",
]