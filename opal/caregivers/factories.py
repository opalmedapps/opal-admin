"""Module providing model factories for caregiver app models."""

from datetime import datetime

from factory import Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker.generator import random
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


class DeviceProvider(BaseProvider):
    """Faker Provider class that generates random values for the Device factory."""

    def device_id(self) -> str:
        """
        Generate a random device_id.

        Returns:
            A random device_id value between 16 and 100 characters in length.
        """
        length = random.randint(16, 100)
        char_choices = [str(digit) for digit in range(9)] + ['a', 'b', 'c', 'd', 'e', 'f']  # 0-9 digits and letters up to 'f' # noqa: WPS221, E501
        chars = [random.choice(char_choices) for _ in range(length)]
        return ''.join(chars)


Faker.add_provider(DeviceProvider)


class Device(DjangoModelFactory):
    """Model factory to create [opal.caregivers.models.Device][] models."""

    class Meta:
        model = models.Device

    caregiver = SubFactory(CaregiverProfile)
    type = models.DeviceType.IOS  # noqa: A003
    device_id = Faker('device_id')


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
    sent_at = datetime.strptime(
        '2022-10-04 11:11:11',
        '%Y-%m-%d %H:%M:%S',
    )
