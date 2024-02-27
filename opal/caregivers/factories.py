"""Module providing model factories for caregiver app models."""
import datetime as dt
import secrets

from django.utils import timezone

from factory import Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker.providers import BaseProvider

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


class TokenProvider(BaseProvider):
    """Faker Provider class that generates random values."""

    def token(self) -> str:
        """Generate a random hex token.

        Returns:
            A random hex token
        """
        return secrets.token_hex(32)


Faker.add_provider(TokenProvider)


class Device(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.Device][] models."""

    class Meta:
        model = models.Device

    caregiver = SubFactory(CaregiverProfile)
    type = models.DeviceType.IOS  # noqa: A003
    device_id = Faker('token')
    push_token = Faker('token')
    is_trusted = Faker('pybool')


class RegistrationCode(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.RegistrationCode][] models."""

    class Meta:
        model = models.RegistrationCode
    # Using string model references to avoid circular import
    relationship = SubFactory('opal.patients.factories.Relationship')
    code = 'code12345678'


class EmailVerification(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.EmailVerification][] models."""

    class Meta:
        model = models.EmailVerification

    caregiver = SubFactory(CaregiverProfile)
    code = '123456'
    email = 'opal@muhc.mcgill.ca'
    sent_at = timezone.now() - dt.timedelta(seconds=10)
