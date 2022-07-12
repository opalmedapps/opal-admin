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
