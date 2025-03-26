"""Constants for modules of the core app."""
import secrets

# minimum length in bytes for secrets.token_urlsafe (32 characters)
ADMIN_PASSWORD_MIN_LENGTH_BYTES = 24
ADMIN_PASSWORD_MIN_LENGTH = len(secrets.token_urlsafe(ADMIN_PASSWORD_MIN_LENGTH_BYTES))
USERNAME_BACKEND_LEGACY = 'opaladmin-backend-legacy'
USERNAME_INTERFACE_ENGINE = 'interface-engine'
USERNAME_LISTENER = 'listener'
USERNAME_LISTENER_REGISTRATION = 'listener-registration'
USERNAME_ORMS = 'orms'

# 40 characters (20 bytes)
# same as length used by DRF for auth token:
# https://github.com/encode/django-rest-framework/blob/master/rest_framework/authtoken/models.py#L37
TOKEN_LENGTH = 40
