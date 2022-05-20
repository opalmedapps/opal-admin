"""Module providing model factories for hospital settings app models."""
from factory.django import DjangoModelFactory

from . import models


class RelationshipType(DjangoModelFactory):
    """Model factory to create [opal.patients.models.RelationshipType][] models."""

    class Meta:
        model = models.RelationshipType

    name = 'Self'
    name_fr = 'Soi'
    description = 'The patient'
    description_fr = 'Le patient'
    start_age = 14
    form_required = False
