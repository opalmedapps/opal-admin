"""Module providing model factories for patients app models.

reference from:

  https://factoryboy.readthedocs.io/en/stable/recipes.html#dependent-objects-foreignkey

  Article about "Many-to-many relation with a `through`"
"""

import datetime

from dateutil.relativedelta import relativedelta
from factory import Sequence, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory

from opal.caregivers.factories import CaregiverProfile
from opal.hospital_settings.factories import Site

from . import models


class RelationshipType(DjangoModelFactory):
    """Model factory to create [opal.patients.models.RelationshipType][] models."""

    class Meta:
        model = models.RelationshipType
        django_get_or_create = ('name',)

    name = 'Caregiver'
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

    first_name = 'Marge'
    last_name = 'Simpson'
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
    start_date = lazy_attribute(lambda relationship: relationship.patient.date_of_birth)
    end_date = datetime.date.today() + relativedelta(years=2)
    reason = ''


class HospitalPatient(DjangoModelFactory):
    """Model factory to create [opal.patients.models.HospitalPatient][] models."""

    class Meta:
        model = models.HospitalPatient

    patient = SubFactory(Patient)
    site = SubFactory(Site)
    mrn = '9999996'
    is_active = True
