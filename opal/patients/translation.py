# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides translation options for patient models."""

from modeltranslation.translator import TranslationOptions, register

from .models import RelationshipType


@register(RelationshipType)
class RelationshipTypeTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `RelationshipType`.

    See [RelationshipType][opal.patients.models.RelationshipType].
    """

    fields = ('name', 'description')
    required_languages = ('en', 'fr')
