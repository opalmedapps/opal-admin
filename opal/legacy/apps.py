"""Module providing configuration for the legacy app."""
from django.apps import AppConfig


class LegacyConfig(AppConfig):
    """The app configuration for the legacy app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.legacy'
