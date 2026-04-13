"""
Base settings for Credit Fund project.
All environment-specific settings inherit from this.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'INSECURE-change-me-in-production')

DEBUG = False

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

# ──────────────────────────────────────────────
# Application definition
# ──────────────────────────────────────────────

INSTALLED_APPS = [
    # Unfold RTL admin (must be before django.contrib.admin)
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'django_filters',
    'django_fsm',
    'django_fsm_log',
    'allauth',
    'allauth.account',
    'guardian',
    'auditlog',
    'django_celery_beat',
    'corsheaders',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.contrib.celery',
    'health_check.contrib.redis',
    'axes',

    # Project apps
    'apps.core',
    'apps.accounts',
    'apps.clients',
    'apps.guarantees',
    'apps.creditframework',
    'apps.collaterals',
    'apps.contracts',
    'apps.notifications',
    'apps.audit',
    'apps.analytics',
    'apps.portal',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'apps.accounts.middleware.CurrentUserMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ──────────────────────────────────────────────
# Database — PostgreSQL everywhere
# ──────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'credit_fund'),
        'USER': os.environ.get('POSTGRES_USER', 'credit_fund'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'credit_fund'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# ──────────────────────────────────────────────
# Custom User model — MUST be set before first migration
# ──────────────────────────────────────────────

AUTH_USER_MODEL = 'accounts.User'

# ──────────────────────────────────────────────
# Authentication backends
# ──────────────────────────────────────────────

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ──────────────────────────────────────────────
# Password validation
# ──────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ──────────────────────────────────────────────
# Internationalization — Persian / RTL
# ──────────────────────────────────────────────

LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fa', 'Persian'),
    ('en', 'English'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ──────────────────────────────────────────────
# Static & Media files
# ──────────────────────────────────────────────

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ──────────────────────────────────────────────
# Default primary key field type
# ──────────────────────────────────────────────

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────────────
# Cache — Redis
# ──────────────────────────────────────────────

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ──────────────────────────────────────────────
# Celery configuration
# ──────────────────────────────────────────────

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ──────────────────────────────────────────────
# Django REST Framework
# ──────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ──────────────────────────────────────────────
# django-allauth
# ──────────────────────────────────────────────

ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_USERNAME_REQUIRED = True

# ──────────────────────────────────────────────
# django-axes (brute-force protection)
# ──────────────────────────────────────────────

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ['username']

# ──────────────────────────────────────────────
# django-guardian
# ──────────────────────────────────────────────

ANONYMOUS_USER_NAME = None

# ──────────────────────────────────────────────
# File upload limits
# ──────────────────────────────────────────────

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# ──────────────────────────────────────────────
# SMS backend (pluggable)
# ──────────────────────────────────────────────

SMS_BACKEND = os.environ.get('SMS_BACKEND', 'apps.notifications.backends.LoggingSMSBackend')

# ──────────────────────────────────────────────
# Unfold Admin Configuration
# ──────────────────────────────────────────────

UNFOLD = {
    "SITE_TITLE": "سامانه ضمانت‌نامه مؤسسه اعتباری",
    "SITE_HEADER": "سامانه ضمانت‌نامه",
    "SITE_SYMBOL": "shield",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "COLORS": {
        "primary": {
            "50": "#eff6ff",
            "100": "#dbeafe",
            "200": "#bfdbfe",
            "300": "#93c5fd",
            "400": "#60a5fa",
            "500": "#3b82f6",
            "600": "#2563eb",
            "700": "#1d4ed8",
            "800": "#1e40af",
            "900": "#1e3a8a",
            "950": "#172554",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "داشبورد",
                "separator": True,
                "items": [
                    {
                        "title": "صفحه اصلی",
                        "icon": "home",
                        "link": "/admin/",
                    },
                ],
            },
            {
                "title": "مدیریت کاربران",
                "separator": True,
                "items": [
                    {
                        "title": "کاربران",
                        "icon": "people",
                        "link": "/admin/accounts/user/",
                    },
                    {
                        "title": "گروه‌ها",
                        "icon": "group",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
            {
                "title": "مدیریت مشتریان",
                "separator": True,
                "items": [
                    {
                        "title": "مشتریان",
                        "icon": "person",
                        "link": "/admin/clients/client/",
                    },
                ],
            },
            {
                "title": "ضمانت‌نامه‌ها",
                "separator": True,
                "items": [
                    {
                        "title": "ضمانت‌نامه‌ها",
                        "icon": "description",
                        "link": "/admin/guarantees/guarantee/",
                    },
                    {
                        "title": "انواع ضمانت‌نامه",
                        "icon": "category",
                        "link": "/admin/guarantees/guaranteetype/",
                    },
                    {
                        "title": "ذینفعان",
                        "icon": "business",
                        "link": "/admin/guarantees/beneficiary/",
                    },
                    {
                        "title": "پرداخت‌ها",
                        "icon": "payments",
                        "link": "/admin/guarantees/payment/",
                    },
                ],
            },
            {
                "title": "چارچوب اعتباری",
                "separator": True,
                "items": [
                    {
                        "title": "ارزیابی اعتباری",
                        "icon": "analytics",
                        "link": "/admin/creditframework/creditevaluation/",
                    },
                    {
                        "title": "سطوح اعتباری",
                        "icon": "layers",
                        "link": "/admin/creditframework/credittier/",
                    },
                    {
                        "title": "عوامل امتیازدهی",
                        "icon": "tune",
                        "link": "/admin/creditframework/scorecardfactor/",
                    },
                ],
            },
            {
                "title": "وثایق",
                "separator": True,
                "items": [
                    {
                        "title": "وثایق",
                        "icon": "account_balance",
                        "link": "/admin/collaterals/collateral/",
                    },
                ],
            },
            {
                "title": "قراردادها",
                "separator": True,
                "items": [
                    {
                        "title": "قراردادها",
                        "icon": "handshake",
                        "link": "/admin/contracts/contract/",
                    },
                    {
                        "title": "قالب‌های اسناد",
                        "icon": "file_copy",
                        "link": "/admin/contracts/documenttemplate/",
                    },
                ],
            },
            {
                "title": "اعلان‌ها و گزارش‌ها",
                "separator": True,
                "items": [
                    {
                        "title": "اعلان‌ها",
                        "icon": "notifications",
                        "link": "/admin/notifications/notification/",
                    },
                    {
                        "title": "لاگ تغییرات",
                        "icon": "history",
                        "link": "/admin/auditlog/logentry/",
                    },
                ],
            },
        ],
    },
}
