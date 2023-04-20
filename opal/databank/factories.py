"""Module providing model factories for databank app models."""
from django.utils import timezone

import factory
from factory.django import DjangoModelFactory

from opal.patients.factories import Patient

from . import models


class DatabankConsent(DjangoModelFactory):
    """Model factory to create [opal.databank.models.DatabankConsent][] models."""

    patient = factory.SubFactory(Patient)
    appointments = factory.Faker('boolean')
    diagnosis = factory.Faker('boolean')
    demographics = factory.Faker('boolean')
    labs = factory.Faker('boolean')
    questionnaires = factory.Faker('boolean')
    last_synchronized = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.DatabankConsent
