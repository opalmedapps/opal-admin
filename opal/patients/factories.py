"""Module providing model factories for patients app models.

reference from:

  https://factoryboy.readthedocs.io/en/stable/recipes.html#dependent-objects-foreignkey

  Article about "Many-to-many relation with a `through`"
"""

import datetime

from factory import RelatedFactory, Sequence, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory

from opal.caregivers.factories import CaregiverProfile
from opal.hospital_settings.factories import Site

from . import models


class RelationshipType(DjangoModelFactory):
    """Model factory to create [opal.patients.models.RelationshipType][] models."""

    class Meta:
        model = models.RelationshipType
        django_get_or_create = ('name',)

    name = 'Self'
    name_fr = lazy_attribute(lambda type: f'{type.name} FR')
    description = 'The patient'
    description_fr = lazy_attribute(lambda type: f'{type.description} FR')
    start_age = 14
    form_required = False
    can_answer_questionnaire = False


class Patient(DjangoModelFactory):
    """Model factory to create [opal.patients.models.Patient][] models."""

    class Meta:
        model = models.Patient
        django_get_or_create = ('ramq',)

    first_name = 'Patient First Name'
    last_name = 'Patient Last Name'
    date_of_birth = datetime.date(1999, 1, 1)
    sex = models.Patient.SexType.MALE
    ramq = ''
    legacy_id = Sequence(lambda number: number + 1)


class Relationship(DjangoModelFactory):
    """Model factory to create [opal.patients.models.Relationship][] models."""

    class Meta:
        model = models.Relationship

    patient = SubFactory(Patient)
    caregiver = SubFactory(CaregiverProfile)
    type = SubFactory(RelationshipType)  # noqa: A003
    request_date = datetime.date.today()
    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 5, 1)
    reason = 'REASON'


class CaregiverWithPatients(CaregiverProfile):
    """Model factory to create caregiverWithPatients models."""

    caregivers = RelatedFactory(
        Relationship,
        factory_related_name='caregiver',
    )


class HospitalPatient(DjangoModelFactory):
    """Model factory to create [opal.patients.models.HospitalPatient][] models."""

    class Meta:
        model = models.HospitalPatient

    patient = SubFactory(Patient)
    site = SubFactory(Site)
    mrn = '9999996'
    is_active = True
