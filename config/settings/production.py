"""
Settings for production.

Inspired by cookiecutter-django: https://cookiecutter-django.readthedocs.io/en/latest/index.html
"""
from .base import *
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env.str('SECRET_KEY')
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# DATABASES
# ------------------------------------------------------------------------------
# don't close the connection after each request
# see https://docs.djangoproject.com/en/dev/ref/databases/#persistent-database-connections
DATABASES['default']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=60)  # noqa: F405
DATABASES['legacy']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=60)  # noqa: F405
DATABASES['questionnaire']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=60)  # noqa: F405

# CACHES
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/topics/cache/
# use in-memory cache for now until there is a need for another caching mechanism
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '',
    },
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)

# STATIC & MEDIA
# ------------------------------------------------------------------------------
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env.str(
    'DEFAULT_FROM_EMAIL',
    default='Opal Backend <noreply@opalmedapps.ca>',
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env.str('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env.str(
    'DJANGO_EMAIL_SUBJECT_PREFIX',
    default='[Opal Backend]',
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = env.str('EMAIL_HOST')
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = env.int('EMAIL_PORT')
# https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
EMAIL_USE_TLS = EMAIL_PORT == 587  # noqa: WPS432
# https://docs.djangoproject.com/en/dev/ref/settings/#email-use-ssl
EMAIL_USE_SSL = not EMAIL_USE_TLS

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}},
    'formatters': {
        'verbose': {
            'format': '{levelname:^8s} {asctime} {module} {process} {thread} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'level': 'ERROR',
            'handlers': ['console', 'mail_admins'],
            'propagate': True,
        },
    },
}

# OPAL SPECIFIC
# ------------------------------------------------------------------------------
# Redirect after logout to legacy OpalAdmin's logout page
# https://docs.djangoproject.com/en/dev/ref/settings/#logout-redirect-url
LOGOUT_REDIRECT_URL = f'{OPAL_ADMIN_URL}/user/logout'  # noqa: F405
