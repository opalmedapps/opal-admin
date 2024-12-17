"""Module providing configuration for the core app."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """The app configuration for the core app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.core'

    def ready(self) -> None:
        """Perform initialization tasks."""
        # Implicitly connect signal handlers decorated with @receiver.
        # See: https://docs.djangoproject.com/en/dev/topics/signals/#connecting-receiver-functions
        from . import signals  # noqa: F401, WPS433
