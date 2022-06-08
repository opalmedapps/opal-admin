"""This module provides configuration for the report settings app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportSettingsConfig(AppConfig):
    """This class provides app configuration for the report settings app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.report_settings'

    verbose_name = _('Report Settings')
