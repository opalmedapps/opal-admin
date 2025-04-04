# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing configuration for the legacy questionnaires app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LegacyQuestionnairesConfig(AppConfig):
    """The app configuration for the legacy questionnaires app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opal.legacy_questionnaires'
    verbose_name = _('Legacy Questionnaires')
