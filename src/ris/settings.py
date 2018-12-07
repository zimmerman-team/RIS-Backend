# Django settings for ris-backend project.

import os
from local_settings import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

API_CACHE_SECONDS = 604800

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'hou6%%$0)i&xn89+*&*h#q7r&dt!u_)#)zzltfm_ea&0_px6*b'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_SERIALIZER_CLASS': (
        'rest_framework.pagination.PageNumberPagination',
    ),
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),

}

# Application definition

INSTALLED_APPS = [
    'after_response',
    'django_rq',
    'rest_auth',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',
    'rest_framework',
    'rest_framework_swagger',
    'rest_framework_docs',
    'task_queue',
    'djsupervisor',
    'django_extensions',
    'debug_toolbar',

    # Social Login
    'rest_framework.authtoken',

    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'rest_auth.registration',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.twitter',
    'allauth.socialaccount.providers.google',

    # Applications
    'subscriptions',
    'generics',
    'accounts',
    'dossier',
    'query',
    'favorite',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_SESSION_LOGIN = False

INTERNAL_IPS = ['127.0.0.1']

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = ('GET', 'POST', 'DELETE', 'PUT')

ROOT_URLCONF = 'ris.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), '..', 'templates').replace('\\', '/')],
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

REST_AUTH_SERIALIZERS = {
    'LOGIN_SERIALIZER': 'accounts.serializers.CustomLoginSerializer',
    'PASSWORD_RESET_SERIALIZER': 'accounts.serializers.PasswordResetSerializer',
}

WSGI_APPLICATION = 'ris.wsgi.application'

# Database

DATABASES = {
    'default': {
        'ENGINE': RIS_DB_ENGINE,
        'HOST': RIS_DB_HOST,
        'PORT': RIS_DB_PORT,
        'NAME': RIS_DB_NAME,
        'USER': RIS_DB_USER,
        'PASSWORD': RIS_DB_PASSWORD,
        'CONN_MAX_AGE': RIS_DB_CONN_MAX_AGE,
    },
}

CACHES = {
    'default': {
        'BACKEND': RIS_CACHES_DEFAULT_BACKEND,
        'LOCATION': RIS_CACHES_DEFAULT_LOCATION,
    }
}

# Password validation

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Email settings

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = RIS_EMAIL_HOST
EMAIL_HOST_USER = RIS_EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = RIS_EMAIL_HOST_PASSWORD
EMAIL_PORT = RIS_EMAIL_PORT
EMAIL_USE_TLS = RIS_EMAIL_USE_TLS
DEFAULT_FROM_EMAIL = RIS_EMAIL_HOST_USER

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_ADAPTER = 'accounts.views.CustomAccountAdapter'

OLD_PASSWORD_FIELD_ENABLED = True
LOGOUT_ON_PASSWORD_CHANGE = False

# Allauth social account providers settings

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'VERIFIED_EMAIL': True,
    }
}

# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Social login

SITE_ID = RIS_SITE_ID

# Queue lines

RQ_REDIS_URL = RIS_RQ_REDIS_URL
RQ_QUEUES = {
    'default': {
        'URL': RQ_REDIS_URL,
        'DEFAULT_TIMEOUT': 3600,
    },
    'doc_scan': {
        'URL': RQ_REDIS_URL,
        'DEFAULT_TIMEOUT': 3600,
    }
}

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/media/'

STATIC_ROOT = os.environ.get('RIS_STATIC_ROOT', os.path.join(os.path.dirname(BASE_DIR), 'media'))
ALLOWED_HOSTS = ['*']

