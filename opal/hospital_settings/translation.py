"""This module provides translation options for hospital-specific settings models."""
from modeltranslation.translator import TranslationOptions, register

from .models import Institution, Site
from .models import HospitalIdentifierType


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


@register(HospitalIdentifierType)
class HospitalIdentifierTypeTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `HospitalIdentifierType`.

    See [HospitalIdentifierType][opal.hospital_settings.models.HospitalIdentifierType].
    """

    fields = ('description',)
    required_languages = ('en', 'fr')
