"""
With these settings, tests run faster.

Inspired by cookiecutter-django: https://cookiecutter-django.readthedocs.io/en/latest/index.html
"""
import django_stubs_ext

from .base import *
from .base import env

# Monkeypatching Django, so stubs will work for all generics
# see: https://github.com/typeddjango/django-stubs/tree/master/django_stubs_ext
django_stubs_ext.monkeypatch()

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env.str(
    'SECRET_KEY',
    default='I1hs8ZDzJIaBFPLviE7SzlPZU8rtMwJyvoKG7EopQD45A39xcF9WwwmZtFaQHkmL',
)
print(SECRET_KEY)

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# django-easy-audit
# ------------------------------------------------------------------------------
# Don't watch model events by default.
# Also helps suppressing data migration errors during test initialization.
DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = False

# Whitenoise
# ------------------------------------------------------------------------------
# Get rid of whitenoise "No directory at" warning, as it's not helpful when running tests.
# Related:
#     - https://github.com/evansd/whitenoise/issues/215
#     - https://github.com/evansd/whitenoise/issues/191
#     - https://github.com/evansd/whitenoise/commit/4204494d44213f7a51229de8bc224cf6d84c01eb
#
# https://whitenoise.readthedocs.io/en/stable/base.html#autorefresh
WHITENOISE_AUTOREFRESH = True
