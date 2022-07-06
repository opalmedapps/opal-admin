"""This module provides translation options for patient models."""
from modeltranslation.translator import TranslationOptions, register

from .models import Patient, Relationship, RelationshipType


@register(Patient)
class PatientTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `Patient`.

    See [Patient][opal.patients.models.Patient].
    """

    fields = ()
    required_languages = ('en', 'fr')


@register(Relationship)
class RelationshipTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `Relationship`.

    See [Relationship][opal.patients.models.Relationship].
    """

    fields = ()
    required_languages = ('en', 'fr')


@register(RelationshipType)
class RelationshipTypeTranslationOptions(TranslationOptions):
    """
    This class provides translation options for `RelationshipType`.

    See [RelationshipType][opal.patients.models.RelationshipType].
    """

    fields = ('name', 'description')
    required_languages = ('en', 'fr')
