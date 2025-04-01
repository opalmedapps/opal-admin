# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing configuration for the legacy app."""

from django.apps import AppConfig


class LegacyConfig(AppConfig):
    """The app configuration for the legacy app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.legacy'
