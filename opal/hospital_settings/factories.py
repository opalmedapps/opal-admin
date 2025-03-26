"""Module providing model factories for patients app models.

reference from:

  https://factoryboy.readthedocs.io/en/stable/recipes.html#dependent-objects-foreignkey

  Article about "Many-to-many relation with a ‘through’"
"""

import datetime

from django.utils.translation import gettext_lazy as _

from factory import Faker, LazyFunction, RelatedFactory, Sequence, SubFactory
from factory.django import DjangoModelFactory

from opal.caregivers.factories import CaregiverProfile

from . import models


def get_relationship_status() -> str:
    """
    Return a random relationship status from available choices.

    Returns:
        the random choice from models.RelationshipStatus
    """
    relationship_status = [status[0] for status in models.RelationshipStatus]
    return relationship_status[0]


class RelationshipType(DjangoModelFactory):
    """Model factory to create [opal.hospital_settings.models.RelationshipType][] models."""

    class Meta:
        model = models.RelationshipType

    name = 'Self'
    name_fr = 'Soi'
    description = 'The patient'
    description_fr = 'Le patient'
    start_age = 14
    form_required = False


class Patient(DjangoModelFactory):
    """Model factory to create [opal.patients.models.Patient][] models."""

    class Meta:
        model = models.Patient

    first_name = Faker(_('first_name'))
    last_name = Faker(_('last_name'))
    day_of_birth = Faker('date_object')
    legacy_id = Sequence(lambda number: number + 1)


class Relationship(DjangoModelFactory):
    """Model factory to create [opal.patients.models.Relationship][] models."""

    class Meta:
        model = models.Relationship

    patient = SubFactory(Patient)
    caregiver = SubFactory(CaregiverProfile)
    relationship_type = SubFactory(RelationshipType)
    status = LazyFunction(get_relationship_status)
    request_date = datetime.date.today()
    start_date = Faker('date_object')
    end_date = Faker('date_object')


class CaregiverWithPatients(CaregiverProfile):
    """Model factory to create caregiverWithPatients models."""

    caregivers = RelatedFactory(
        Relationship,
        factory_related_name='caregiver',
    )
