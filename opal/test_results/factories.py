"""Module providing model factories for test result app models."""
from django.utils import timezone

import factory
from factory.django import DjangoModelFactory

from opal.patients.factories import Patient

from . import models


class GeneralTest(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.GeneralTest][] models.

    Test group code and description depend on the test type.
    """

    patient = factory.SubFactory(Patient)
    type = factory.Iterator(models.TestType.values)  # noqa: A003
    collected_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    received_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    reported_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    message_type = 'ORU'
    message_event = 'R01'
    # Adjust the code and description based on test type
    # Pathology always has RQSTPTISS code, labs can have many different possible codes
    test_group_code: str = factory.LazyAttribute(
        lambda test: 'RQSTPTISS'
        if test.type == models.TestType.PATHOLOGY
        else 'CBC',
    )
    test_group_code_description: str = factory.LazyAttribute(
        lambda test: 'Request Pathology Tissue'
        if test.type == models.TestType.PATHOLOGY
        else 'COMPLETE BLOOD COUNT',
    )
    legacy_document_id = factory.Sequence(lambda number: number + 1)

    class Meta:
        model = models.GeneralTest


class PathologyObservationFactory(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.PathologyObservation][] models."""

    general_test = factory.SubFactory(GeneralTest, type=models.TestType.PATHOLOGY)
    identifier_code = 'SPSPECI'
    identifier_text = 'SPECIMEN'
    value = "Left breast mass three o'clock previously collagenous stroma"
    observed_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.PathologyObservation


class LabObservationFactory(DjangoModelFactory):
    """Model factory to create LabObservations models."""

    general_test = factory.SubFactory(GeneralTest, type=models.TestType.LAB)
    identifier_code = 'WBC'
    identifier_text = 'WHITE BLOOD CELL'
    value = 30.02
    value_units = '10^9/L'
    value_abnormal = factory.Iterator(models.AbnormalFlag.values)
    value_min_range = 3.0
    value_max_range = 15.0
    observed_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.LabObservation


class Note(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.Note][] models."""

    general_test = factory.SubFactory(GeneralTest)
    note_source = 'Signature Line'
    note_text = factory.Faker('paragraph', nb_sentences=3)

    class Meta:
        model = models.Note
