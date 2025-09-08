# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Django base settings to build other settings files upon.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/

Inspired by cookiecutter-django: https://cookiecutter-django.readthedocs.io/en/latest/index.html
"""

from pathlib import Path
from typing import Any

from django.utils.translation import gettext_lazy as _

import django_stubs_ext
import environ
import structlog

# Monkeypatching Django, so stubs will work for all generics
# see: https://github.com/typeddjango/django-stubs/tree/master/ext
django_stubs_ext.monkeypatch()

# get root of the project
ROOT_DIR = Path(__file__).resolve(strict=True).parents[2]
APPS_DIR = ROOT_DIR / 'opal'

env = environ.Env()
# OS environment variables take precedence over variables from .env
environ.Env.read_env(str(ROOT_DIR / '.env'))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG: bool = env.bool('DEBUG', default=False)
# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
#
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = 'America/Toronto'
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-ca'
# https://docs.djangoproject.com/en/dev/ref/settings/#languages
# Provide a type hint to avoid mypy import cycle errors
# see: https://github.com/typeddjango/django-stubs/issues/1346
LANGUAGES: list[tuple[str, django_stubs_ext.StrPromise]] = [
    ('en', _('English')),
    ('fr', _('French')),
]
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / 'locale')]
# https://docs.djangoproject.com/en/dev/ref/settings/#silenced-system-checks
# W001: allow definition of PAGE_SIZE globally while having pagination opt-in
# E311: legacy questionnaire content_id cannot be unique
# see also: https://code.djangoproject.com/ticket/26472
SILENCED_SYSTEM_CHECKS = ['rest_framework.W001', 'fields.E311']


# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
        'TEST': {
            'NAME': f'test_{env("DATABASE_NAME")}',
        },
        'ATOMIC_REQUESTS': True,
    },
    'legacy': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'OpalDB',
        'USER': env('LEGACY_DATABASE_USER'),
        'PASSWORD': env('LEGACY_DATABASE_PASSWORD'),
        'HOST': env('LEGACY_DATABASE_HOST'),
        'PORT': env('LEGACY_DATABASE_PORT'),
        'TIME_ZONE': 'America/Toronto',
        'TEST': {
            'NAME': 'test_OpalDB',
        },
    },
    'questionnaire': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'QuestionnaireDB',
        'USER': env('LEGACY_DATABASE_USER'),
        'PASSWORD': env('LEGACY_DATABASE_PASSWORD'),
        'HOST': env('LEGACY_DATABASE_HOST'),
        'PORT': env('LEGACY_DATABASE_PORT'),
        'TIME_ZONE': 'America/Toronto',
        'TEST': {
            'NAME': 'test_QuestionnaireDB',
        },
    },
}

# Use SSL for all the database connections if DATABASE_USE_SSL is set to True
if env.bool('DATABASE_USE_SSL', default=False):  # pragma: no cover
    # Use OPTIONS setting to set extra parameters when connecting to the database.
    # The parameters vary depending on the database backend.
    # For more information see MySQL attributes/options (according to Django's docs, same options for MariaDB):
    #    - https://docs.djangoproject.com/en/4.2/ref/databases/#connecting-to-the-database
    #    - https://mysqlclient.readthedocs.io/user_guide.html#functions-and-attributes
    ssl_settings = {
        # For the "ssl_mode" parameters see MySQL's documentation:
        # https://dev.mysql.com/doc/refman/8.0/en/connection-options.html#option_general_ssl-mode
        # The following links might be helpful in case we need to modify the sources of the mysqlclient dependency:
        #    - https://dev.mysql.com/doc/c-api/8.0/en/mysql-options.html
        #    - https://mariadb.com/kb/en/mysql_optionsv/
        'ssl_mode': 'VERIFY_IDENTITY',
        # See mysql_ssl_set MySQL C API where the parameter names are keys used by the "ssl" setting.
        # https://dev.mysql.com/doc/c-api/8.0/en/mysql-ssl-set.html
        # The current setup is using one-way SSL/TLS.
        # https://mariadb.com/kb/en/securing-connections-for-client-and-server/#enabling-one-way-tls-for-mariadb-clients
        # TODO: two-way SSL/TLS
        'ssl': {
            'ca': env.str('SSL_CA'),
        },
    }

    DATABASES['default']['OPTIONS'] = ssl_settings
    DATABASES['legacy']['OPTIONS'] = ssl_settings
    DATABASES['questionnaire']['OPTIONS'] = ssl_settings

# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DATABASE_ROUTERS
DATABASE_ROUTERS = ['opal.core.dbrouters.LegacyDbRouter']

# Default primary key field
# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
# See also: https://docs.djangoproject.com/en/dev/releases/dev/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'config.urls'
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'
# Root path for API URLs
# Note: without a trailing slash
API_ROOT = 'api'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    # modeltranslation must come before admin
    # https://django-modeltranslation.readthedocs.io/en/latest/installation.html#installed-apps
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django_filters',
    'django_tables2',
    'corsheaders',
    'auditlog',
    'django_structlog',
    'slippers',
    'phonenumber_field',
    'drf_spectacular',
]

LOCAL_APPS = [
    'opal.core',
    'opal.hospital_settings',
    'opal.users',
    'opal.caregivers',
    'opal.patients',
    'opal.legacy',
    'opal.legacy_questionnaires',
    'opal.questionnaires',
    'opal.health_data',
    'opal.databank',
    'opal.test_results',
    'opal.pharmacy',
    'opal.usage_statistics',
]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = 'start'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = 'login'
# routes ignored by LoginRequiredMiddleware
AUTH_EXEMPT_ROUTES = ['login', 'admin:login', 'admin:index', 'favicon.ico']
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
# also: https://docs.djangoproject.com/en/dev/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = 'users.User'

# fedauth webservice API
if env.get_value('FEDAUTH_API_ENDPOINT', default=None):  # pragma: no cover
    FEDAUTH_API_ENDPOINT = env.url('FEDAUTH_API_ENDPOINT').geturl()
    FEDAUTH_INSTITUTION = env.str('FEDAUTH_INSTITUTION')

    AUTHENTICATION_BACKENDS.append('opal.core.auth.FedAuthBackend')

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
# https://docs.djangoproject.com/en/dev/topics/auth/passwords/#enabling-password-validation
AUTH_PASSWORD_VALIDATORS: list[dict[str, Any]] = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # CorsMiddleware should be placed as high as possible, definitely before CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'opal.core.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'opal.core.middleware.AuditlogMiddleware',
]

# STATIC
# https://docs.djangoproject.com/en/dev/howto/static-files/
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR / 'staticfiles')
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / 'static')]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# MEDIA
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/howto/static-files/deployment/
# See https://docs.djangoproject.com/en/dev/howto/static-files/#serving-files-uploaded-by-a-user-during-development
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / 'media')
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [str(APPS_DIR / 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.media',
                'opal.core.context_processors.opal_global_settings',
                'opal.core.context_processors.current_app',
            ],
            # make slippers available in all templates
            'builtins': ['slippers.templatetags.slippers'],
        },
    },
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = 'django.forms.renderers.DjangoTemplates'

# transitional setting in preparation for Django 6
FORMS_URLFIELD_ASSUME_HTTPS = True

# Crispy forms
# https://django-crispy-forms.readthedocs.io/en/latest/index.html
#
# Use Twitter Bootstrap (version 5) as a default template for the project
# https://django-crispy-forms.readthedocs.io/en/latest/layouts.html#overriding-project-templates
# Override allowed template packs for bootstrap5
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
# Make crispy fail loud in debug
# https://django-crispy-forms.readthedocs.io/en/latest/crispy_tag_forms.html#make-crispy-forms-fail-loud
CRISPY_FAIL_SILENTLY = not DEBUG

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
# Allow legacy OpalAdmin to read CSRF cookie to facilitate logout
CSRF_COOKIE_HTTPONLY = False
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = 'DENY'

# EMAIL
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/topics/email/
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5
EMAIL_FROM_REGISTRATION = 'Opal Registration <registration@opalmedapps.ca>'

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = 'admin/'
# TODO: fill out or move to .env
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
# ADMINS =
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
# MANAGERS = ADMINS  # noqa: ERA001

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# See also:
# https://sobolevn.me/2020/03/do-not-log
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        # Console Output: https://www.structlog.org/en/stable/console-output.html
        'console': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'django_structlog': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'opal': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # Suppress default django runserver logs
        'django.request': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Auditing
# ------------------------------------------------------------------------------

# django-structlog configuration
# https://django-structlog.readthedocs.io/en/latest/getting_started.html#installation
# https://www.structlog.org/en/stable/configuration.html
# ------------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# django-auditlog
# ------------------------------------------------------------------------------
# See https://django-auditlog.readthedocs.io/en/latest/usage.html#settings
AUDITLOG_INCLUDE_ALL_MODELS = True
# Store changes in JSON format
AUDITLOG_STORE_JSON_CHANGES = True
# Use the Appuserid header to correlate changes with app users
# https://django-auditlog.readthedocs.io/en/latest/usage.html#correlation-id
AUDITLOG_CID_HEADER = 'Appuserid'

# OPAL SPECIFIC
# ------------------------------------------------------------------------------
# Legacy OpalAdmin related settings
#
# base URL to old OpalAdmin (no trailing slash)
OPAL_ADMIN_URL = env.url('OPAL_ADMIN_URL').geturl()

# Source System/Integration Engine
SOURCE_SYSTEM_HOST = env.url('SOURCE_SYSTEM_HOST').geturl()
SOURCE_SYSTEM_USER = env('SOURCE_SYSTEM_USER')
SOURCE_SYSTEM_PASSWORD = env('SOURCE_SYSTEM_PASSWORD')

# Registration
# Opal User Registration URL
OPAL_USER_REGISTRATION_URL = env.url('OPAL_USER_REGISTRATION_URL').geturl()
# Institution code for registration
INSTITUTION_CODE = env.str('INSTITUTION_CODE')

# Questionnaires: Export Report
# List of accounts to be excluded from the questionnaires list when not in debug mode
TEST_PATIENTS = env.list('TEST_PATIENT_QUESTIONNAIREDB_IDS', default=[])
# Name of the source system that generated PDF report
REPORT_SOURCE_SYSTEM = env.str('REPORT_SOURCE_SYSTEM')
# Number assigned by the hospital for the generated PDF report
REPORT_DOCUMENT_NUMBER = env.str('REPORT_DOCUMENT_NUMBER')

# ORMS SETTINGS
# Name of the group for the ORMS users
# Please see: https://docs.djangoproject.com/en/dev/topics/auth/default/#groups
ORMS_GROUP_NAME = 'ORMS Users'
ORMS_ENABLED = env.bool('ORMS_ENABLED', default=False)

if ORMS_ENABLED:
    # base URL to ORMS (no trailing slash)
    ORMS_HOST = env.url('ORMS_HOST').geturl()

# OTHER
ADMIN_GROUP_NAME = 'System Administrators'
USER_MANAGER_GROUP_NAME = 'User Managers'
REGISTRANTS_GROUP_NAME = 'Registrants'

# Sending SMS message settings

SMS_ENABLED = env.bool('SMS_ENABLED')

if SMS_ENABLED:
    TWILIO_ACCOUNT_SID = env.str('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = env.str('TWILIO_AUTH_TOKEN')
    SMS_FROM = env.str('SMS_FROM')

# PATHOLOGY REPORTS SETTINGS
# Path to the pathology reports folder
PATHOLOGY_REPORTS_PATH = Path(env.str('PATHOLOGY_REPORTS_PATH'))

# Databank Enabled
DATABANK_ENABLED = env.bool('DATABANK_ENABLED')

# Third party apps settings
# ------------------------------------------------------------------------------
#
# django-rest-framework
# ------------------------------------------------------------------------------
# See https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    # lock down API by default, override on a per-view basis (see Two Scoops of Django Section 17.2)
    'DEFAULT_PERMISSION_CLASSES': [
        'opal.core.drf_permissions.IsSuperUser',
    ],
    # disabled pagination by default
    # use rest_framework.pagination.PageNumberPagination to enable for specific endpoints
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    # set default request format to JSON
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular API documentation (OpenAPI 3.0 Specification)
# See https://drf-spectacular.readthedocs.io/en/latest/index.html
SPECTACULAR_SETTINGS = {
    'TITLE': 'Opal Backend',
    'DESCRIPTION': (
        'This Python Django-based backend provides API '
        + 'endpoints for other Opal applications and a user '
        + 'interface for administrative functionality.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'ENUM_NAME_OVERRIDES': {
        'RelationshipStatusEnum': 'opal.patients.models.RelationshipStatus.choices',
        'RegistrationCodeStatusEnum': 'opal.caregivers.models.RegistrationCodeStatus.choices',
    },
    # list of authentication/permission classes for spectacular's views.
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAdminUser'],
    #  TODO: 'CONTACT': {},
    #  TODO: 'LICENSE': {},
}

# django-cors-headers
# ------------------------------------------------------------------------------
# See https://github.com/adamchainz/django-cors-headers#setup
# A list of origins that are authorized to make cross-site HTTP requests.
# CORS settings are optional
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)

# django-phonenumber-field
# ------------------------------------------------------------------------------
# See: https://django-phonenumber-field.readthedocs.io/en/latest/reference.html#settings
PHONENUMBER_DEFAULT_REGION = 'CA'
PHONENUMBER_DEFAULT_FORMAT = 'INTERNATIONAL'
PHONENUMBER_DB_FORMAT = 'INTERNATIONAL'

# django-tables2
# ------------------------------------------------------------------------------
#
# See https://django-tables2.readthedocs.io/en/latest/pages/custom-rendering.html
# Set a default template to use
DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap5-responsive.html'
# Default CSS classes for tables
DJANGO_TABLES2_TABLE_ATTRS = {
    'class': 'table table-hover',
    'thead': {
        'class': 'table-light',
    },
}
