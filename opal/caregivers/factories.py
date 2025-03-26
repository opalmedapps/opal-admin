"""Module providing model factories for caregiver app models."""

import datetime

from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from opal.users.factories import Caregiver

from . import models


class CaregiverProfile(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.CaregiverProfile][] models."""

    class Meta:
        model = models.CaregiverProfile

    user = SubFactory(Caregiver)
    legacy_id = Sequence(lambda number: number + 1)


class RegistrationCode(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.RegistrationCode][] models."""

    class Meta:
        model = models.RegistrationCode
    # Using string model references to avoid circular import
    relationship = SubFactory('opal.patients.factories.Relationship')
    code = 'code12345678'
    status = models.RegistrationCodeStatus.NEW
    email_verification_code = '123456'
    creation_date = datetime.date.today()
