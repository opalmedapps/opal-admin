"""Module providing configuration for the services app."""
from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """The app configuration for the services app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services'
