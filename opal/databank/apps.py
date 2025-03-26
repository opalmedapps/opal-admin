"""Module providing configuration for the databank app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DatabankConfig(AppConfig):
    """The app configuration for the databank app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.databank'
    verbose_name = _('Databank')
