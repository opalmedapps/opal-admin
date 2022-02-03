"""This module provides configuration for the hospital-specific settings app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HospitalSettingsConfig(AppConfig):
    """This class provides app configuration for the hospital-specific settings app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.hospital_settings'

    verbose_name = _('Hospital Settings')
