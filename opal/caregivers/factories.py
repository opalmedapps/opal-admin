"""Module providing model factories for caregiver app models."""

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


class SecurityQuestion(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.SecurityQuestion][] models."""

    class Meta:
        model = models.SecurityQuestion

    title = 'Apple'
    title_fr = 'Pomme'


class SecurityAnswer(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.SecurityAnswer][] models."""

    class Meta:
        model = models.SecurityAnswer

    question = 'Apple'
    user = SubFactory(CaregiverProfile)
    answer = 'answer'


class RegistrationCode(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.RegistrationCode][] models."""

    class Meta:
        model = models.RegistrationCode
    # Using string model references to avoid circular import
    relationship = SubFactory('opal.patients.factories.Relationship')
    code = 'code12345678'
    email_verification_code = '123456'
