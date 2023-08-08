"""Module providing model factories for test result app models."""
from django.utils import timezone

import factory
from factory.django import DjangoModelFactory

from opal.patients.factories import Patient

from . import models


class GeneralTestFactory(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.GeneralTest][] models."""

    patient = factory.SubFactory(Patient)
    type = factory.Iterator(models.TestType.values)  # noqa: A003
    collected_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    received_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    message_type = 'ORU'
    message_event = 'R01'
    test_group_code = 'RQSTPTISS'
    test_group_code_description = 'Request Pathology Tissue'
    legacy_document_id = factory.Sequence(lambda number: number + 1)

    class Meta:
        model = models.GeneralTest


class ObservationFactory(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.Observation][] models."""

    general_test = factory.SubFactory(GeneralTestFactory)
    identifier_code = 'SPSPECI'
    identifier_text = 'SPECIMEN'
    value = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=0)
    value_units = 'mg'
    value_abnormal = factory.Iterator(models.AbnormalFlag.values)
    observed_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.Observation
