# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides admin options for databank models."""

from django.contrib import admin

from . import models


@admin.register(models.DatabankConsent)
class DatabankConsentAdmin(admin.ModelAdmin[models.DatabankConsent]):
    """The admin class for `DatabankConsent` models."""

    list_display = [
        '__str__',
        'has_appointments',
        'has_diagnoses',
        'has_demographics',
        'has_labs',
        'has_questionnaires',
        'consent_granted',
        'last_synchronized',
    ]
