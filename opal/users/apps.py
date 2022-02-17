"""Module providing configuration for the users app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """The app configuration for the users app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.users'
    verbose_name = _('Users')
