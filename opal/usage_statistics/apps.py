# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing configuration for the usage statistics app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsageStatisticsConfig(AppConfig):
    """The app configuration for the usage statistics app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.usage_statistics'
    verbose_name = _('Usage Statistics')
