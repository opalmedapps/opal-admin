# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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
        from . import signals  # noqa: F401, PLC0415
