# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides admin options for questionnaire models."""

from django.contrib import admin

from . import models

admin.site.register(models.QuestionnaireProfile, admin.ModelAdmin)
