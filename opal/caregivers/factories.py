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

    title = '1234567'
    is_active = True


class SecurityAnswer(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.SecurityAnswer][] models."""

    class Meta:
        model = models.SecurityAnswer

    question = '1234567'
    profile = SubFactory(CaregiverProfile)
    answer = 'abcdefg'
