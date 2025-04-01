# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides translation options for caregiver models."""

from modeltranslation.translator import TranslationOptions, register

from .models import SecurityQuestion


@register(SecurityQuestion)
class SecurityQuestionTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `SecurityQuestion`.

    See [SecurityQuestion][opal.caregivers.models.SecurityQuestion].
    """

    fields = ('title',)
    required_languages = ('en', 'fr')
