"""Module providing configuration for the caregivers app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CaregiversConfig(AppConfig):
    """The app configuration for the caregivers app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.caregivers'
    verbose_name = _('Caregivers')
