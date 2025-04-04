# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing configuration for the databank app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DatabankConfig(AppConfig):
    """The app configuration for the databank app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.databank'
    verbose_name = _('Databank')
