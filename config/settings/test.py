"""
With these settings, tests run faster.

Inspired by cookiecutter-django: https://cookiecutter-django.readthedocs.io/en/latest/index.html
"""

from .base import *  # noqa: F403, WPS347
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    'SECRET_KEY',
    default='I1hs8ZDzJIaBFPLviE7SzlPZU8rtMwJyvoKG7EopQD45A39xcF9WwwmZtFaQHkmL',
)

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]['OPTIONS']['debug'] = True  # type: ignore[index] # noqa: F405

# django-easy-audit
# ------------------------------------------------------------------------------
# Don't watch model events by default.
# Also helps suppressing data migration errors during test initialization.
DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = False
