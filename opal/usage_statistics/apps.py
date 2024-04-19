"""Module providing configuration for the usage statistics app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsageStatisticsConfig(AppConfig):
    """The app configuration for the usage statistics app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.usage_statistics'
    verbose_name = _('Usage Statistics')
