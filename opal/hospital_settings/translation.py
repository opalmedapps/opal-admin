"""This module provides translation options for hospital-specific settings models."""
from modeltranslation.translator import TranslationOptions, register

from .models import Institution, Site, CaregiverRelationships


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


@register(CaregiverRelationships)
class CaregiverRelationshipsTranslationOptions(TranslationOptions):
    """This class provides translation options for ``CaregiverRelationships``."""

    fields = ('name', 'description')
