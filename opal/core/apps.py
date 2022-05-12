"""Module providing configuration for the core app."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """The app configuration for the core app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.core'
