"""This module provides translation options for caregiver models."""
from modeltranslation.translator import TranslationOptions, register

from .models import SecurityAnswer, SecurityQuestion


@register(SecurityQuestion)
class SecurityQuestionTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `SecurityQuestion`.

    See [SecurityQuestion][opal.caregivers.models.SecurityQuestion].
    """

    fields = ('title',)
    required_languages = ('en', 'fr')


@register(SecurityAnswer)
class SSecurityAnswerTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `SecurityAnswer`.

    See [SecurityAnswer][opal.caregivers.models.SecurityAnswer].
    """

    fields = ('question', 'answer')
    required_languages = ('en', 'fr')
