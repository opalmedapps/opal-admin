"""Module providing model factories for test result app models."""
from typing import Any

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


class Observation(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.Observation][] models.

    The identifiers, value, & value_units fields depend on the parent GeneralTest type.
    If type=Pathology, value is a qualitative description of the tissue sample.
    If type=Labs, value is an integer value for this observation component, in our case a White Blood Cell Count.
    """

    general_test = factory.SubFactory(GeneralTest)
    identifier_code: str = factory.LazyAttribute(
        lambda obx: 'SPSPECI'
        if obx.general_test.type == models.TestType.PATHOLOGY
        else 'WBC',
    )
    identifier_text: str = factory.LazyAttribute(
        lambda obx: 'SPECIMEN'
        if obx.general_test.type == models.TestType.PATHOLOGY
        else 'WHITE BLOOD CELL',
    )
    # Value is the pathology description if pathology, else an integer value for a lab component
    value: Any = factory.LazyAttribute(
        lambda obx: "Left breast mass three o'clock previously collagenous stroma"
        if obx.general_test.type == models.TestType.PATHOLOGY
        else 30.02,
    )
    value_units: str = factory.LazyAttribute(
        lambda obx: ''
        if obx.general_test.type == models.TestType.PATHOLOGY
        else '10^9/L',
    )
    value_abnormal = factory.Iterator(models.AbnormalFlag.values)
    observed_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.Observation


class Note(DjangoModelFactory):
    """Model factory to create [opal.test_results.models.Note][] models."""

    general_test = factory.SubFactory(GeneralTest)
    note_source = 'Signature Line'
    note_text = factory.Faker('paragraph', nb_sentences=3)

    class Meta:
        model = models.Note
