"""Module providing model factories for health data app models."""
from django.utils import timezone

import factory
from factory.django import DjangoModelFactory

from opal.patients.factories import Patient

from . import models


class QuantitySample(DjangoModelFactory):
    """Model factory to create [opal.health_data.models.QuantitySample][] models."""

    patient = factory.SubFactory(Patient)
    start_date = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    device = 'Test Device'
    source = models.SampleSourceType.PATIENT
    type = factory.Iterator(models.QuantitySampleType.values)  # noqa: A003
    value = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=0)
    viewed_at = None
    viewed_by = ''

    class Meta:
        model = models.QuantitySample
