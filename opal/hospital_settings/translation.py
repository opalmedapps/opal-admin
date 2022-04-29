"""This module provides translation options for hospital-specific settings models."""
from modeltranslation.translator import TranslationOptions, register

from .models import Institution, RelationshipType, Site


@register(Institution)
class InstitutionTranslationOptions(TranslationOptions):
    """This class provides translation options for [Institution][opal.hospital_settings.models.Institution]."""

    fields = ('name',)
    required_languages = ('en', 'fr')


@register(Site)
class SiteTranslationOptions(TranslationOptions):
    """This class provides translation options for [Site][opal.hospital_settings.models.Site]."""

    fields = ('name', 'parking_url', 'direction_url')
    required_languages = ('en', 'fr')


@register(RelationshipType)
class RelationshipTypeTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `RelationshipType`.

    See [RelationshipType][opal.hospital_settings.models.RelationshipType].
    """

    fields = ('name', 'description')
    required_languages = ('en', 'fr')
