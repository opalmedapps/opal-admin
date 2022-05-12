"""Module providing configuration for the patients app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PatientsConfig(AppConfig):
    """The app configuration for the patients app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.patients'
    verbose_name = _('Patients')
