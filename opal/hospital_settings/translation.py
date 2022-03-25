"""This module provides translation options for hospital-specific settings models."""
from modeltranslation.translator import TranslationOptions, register

from .models import Institution, Site


@register(Institution)
class InstitutionTranslationOptions(TranslationOptions):
    """This class provides translation options for ``Institution``."""

    fields = ('name',)


@register(Site)
class SiteTranslationOptions(TranslationOptions):
    """This class provides translation options for ``Site``."""

    fields = ('name', 'parking_url', 'direction_url')
