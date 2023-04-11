"""Module providing configuration for the health data app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HealthDataConfig(AppConfig):
    """The app configuration for the health data app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.health_data'
    verbose_name = _('Health Data')
