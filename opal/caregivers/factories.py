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


class SecurityQuestion(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.SecurityQuestion][] models."""

    class Meta:
        model = models.SecurityQuestion

    question_en = 'question_one'
    question_fr = 'question_un'
    created_at = datetime.date(2022, 6, 6)
    updated_at = datetime.date(2022, 6, 6)
    is_active = 1


class SecurityAnswer(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.SecurityAnswer][] models."""

    class Meta:
        model = models.SecurityAnswer

    question = SubFactory(SecurityQuestion)
    profile = SubFactory(CaregiverProfile)
    answer = 'abcdefg'
    created_at = datetime.date(2022, 6, 6)
    updated_at = datetime.date(2022, 6, 6)
