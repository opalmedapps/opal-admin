"""
Django base settings to build other settings files upon.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/

Inspired by cookiecutter-django: https://cookiecutter-django.readthedocs.io/en/latest/index.html
"""
from pathlib import Path

from django.utils.translation import gettext_lazy as _

import django_stubs_ext
import environ

# Monkeypatching Django, so stubs will work for all generics
# see: https://github.com/typeddjango/django-stubs/tree/master/django_stubs_ext
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
            'NAME': 'test_{0}'.format(env('DATABASE_NAME')),
        },
        'ATOMIC_REQUESTS': True,
    },
    'legacy': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('LEGACY_DATABASE_NAME'),
        'USER': env('LEGACY_DATABASE_USER'),
        'PASSWORD': env('LEGACY_DATABASE_PASSWORD'),
        'HOST': env('LEGACY_DATABASE_HOST'),
        'PORT': env('LEGACY_DATABASE_PORT'),
        'TIME_ZONE': 'EST5EDT',
        'TEST': {
            'NAME': 'test_{0}'.format(env('LEGACY_DATABASE_NAME')),
        },
    },
    'questionnaire': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('LEGACY_QUESTIONNAIRE_DATABASE_NAME'),
        'USER': env('LEGACY_DATABASE_USER'),
        'PASSWORD': env('LEGACY_DATABASE_PASSWORD'),
        'HOST': env('LEGACY_DATABASE_HOST'),
        'PORT': env('LEGACY_DATABASE_PORT'),
        'TIME_ZONE': 'EST5EDT',
        'TEST': {
            'NAME': 'test_{0}'.format(env('LEGACY_QUESTIONNAIRE_DATABASE_NAME')),
        },
    },
}

# Use SSL for all the database connections if DATABASE_USE_SSL is set to True
if env.bool('DATABASE_USE_SSL'):  # pragma: no cover
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
    'easyaudit',
    'formtools',
    'slippers',
    'fontawesomefree',
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
]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'opal.core.auth.FedAuthBackend',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = 'start'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = 'login'
# routes ignored by LoginRequiredMiddleware
AUTH_EXEMPT_ROUTES = env.tuple('AUTH_EXEMPT_ROUTES')
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
# also: https://docs.djangoproject.com/en/dev/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = 'users.User'
# fedauth webservice API
FEDAUTH_API_ENDPOINT = env.url('FEDAUTH_API_ENDPOINT').geturl()
FEDAUTH_INSTITUTION = env.str('FEDAUTH_INSTITUTION')

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
AUTH_PASSWORD_VALIDATORS = [
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
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
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
FORM_RENDERER = 'django.forms.renderers.DjangoDivFormRenderer'

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
# MANAGERS = ADMINS  # noqa: E800

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# See also:
# https://sobolevn.me/2020/03/do-not-log
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname:^8s} {name:<28s} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {'level': 'INFO', 'handlers': ['console']},
}

# OPAL SPECIFIC
# ------------------------------------------------------------------------------
# Legacy OpalAdmin related settings
#
# base URL to old OpalAdmin (no trailing slash)
OPAL_ADMIN_URL = env.url('OPAL_ADMIN_URL').geturl()

# Legacy URL for generating questionnaires report
LEGACY_QUESTIONNAIRES_REPORT_URL = env.url('LEGACY_QUESTIONNAIRES_REPORT_URL').geturl()

# Opal Integration Engine (OIE)
OIE_HOST = env.url('OIE_HOST').geturl()
OIE_USER = env('OIE_USER')
OIE_PASSWORD = env('OIE_PASSWORD')

# Registration
# Opal User Registration URL
OPAL_USER_REGISTRATION_URL = env.url('OPAL_USER_REGISTRATION_URL').geturl()
# Institution code for registration
INSTITUTION_CODE = env.str('INSTITUTION_CODE')

# Questionnaires: Export Report
# List of accounts to be excluded from the questionnaires list when not in debug mode
TEST_PATIENTS = env.list('TEST_PATIENT_QUESTIONNAIREDB_IDS', default=[])

# ORMS SETTINGS
# Name of the group for the ORMS users
# Please see: https://docs.djangoproject.com/en/dev/topics/auth/default/#groups
ORMS_GROUP_NAME = 'ORMS Users'
# base URL to ORMS (no trailing slash)
ORMS_HOST = env.url('ORMS_HOST').geturl()
ORMS_USER = env('ORMS_USER')
ORMS_PASSWORD = env('ORMS_PASSWORD')

# OTHER
ADMIN_GROUP_NAME = 'System Administrators'
USER_MANAGER_GROUP_NAME = 'User Managers'
REGISTRANTS_GROUP_NAME = 'Registrants'

# Sending SMS message settings
TWILIO_ACCOUNT_SID = env.str('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env.str('TWILIO_AUTH_TOKEN')
SMS_FROM = env.str('SMS_FROM')

# PATHOLOGY REPORTS SETTINGS
# Path to the pathology reports folder
PATHOLOGY_REPORTS_PATH = Path(env.str('PATHOLOGY_REPORTS_PATH'))

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
    # require specific model permissions (including view) to access API
    'DEFAULT_PERMISSION_CLASSES': [
        'opal.core.drf_permissions.CustomDjangoModelPermissions',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

# django-cors-headers
# ------------------------------------------------------------------------------
# See https://github.com/adamchainz/django-cors-headers#setup
# A list of origins that are authorized to make cross-site HTTP requests.
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS')
# See: https://github.com/adamchainz/django-cors-headers#cors_urls_regex-str--patternstr
CORS_URLS_REGEX = '^/api/.*$'

# django-easy-audit
# ------------------------------------------------------------------------------
# See https://github.com/soynatan/django-easy-audit#settings
# Remove /admin to log requests to the admin site
DJANGO_EASY_AUDIT_UNREGISTERED_URLS_DEFAULT = ['^/admin/jsi18n/', '^/static/', '^/favicon.ico$']
# Make events read-only to disallow deleting
DJANGO_EASY_AUDIT_READONLY_EVENTS = True

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
