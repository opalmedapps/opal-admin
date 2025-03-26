"""Module prividing model factories for pharmacy models."""
from django.utils import timezone

import factory
from factory.django import DjangoModelFactory

from opal.patients.factories import Patient

from . import models


class CodedElementFactory(DjangoModelFactory):
    """Model factory to create [opal.pharmacy.models.CodedElement][] models."""

    identifier = factory.Faker('word')
    text = factory.Faker('word')
    coding_system = factory.Faker('word')
    alternate_identifier = factory.Faker('word')
    alternate_text = factory.Faker('word')
    alternate_coding_system = factory.Faker('word')

    class Meta:
        model = models.CodedElement


class PhysicianPrescriptionOrderFactory(DjangoModelFactory):
    """Model factory to create [opal.pharmacy.models.PhysicianPrescriptionOrder][] models."""

    patient = factory.SubFactory(Patient)
    visit_number = factory.Sequence(lambda number: number + 1)
    quantity = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=0)
    unit = 'mg'
    interval_pattern = 'PRN'  # Take as needed
    interval_duration = ''
    duration = 'INDEF'  # Indefinately
    service_start = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    service_end = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    priority = 'PRN'  # As needed
    trigger_event = 'NW'  # New order, can also be 'XX' order changed
    filler_order_number = factory.Sequence(lambda number: number + 1)
    order_status = 'SC'  # In progress / Scheduled
    entered_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    entered_by = 'John Doe'
    verified_by = 'Jane Doe'
    ordered_by = 'Dr. Doe Doe'
    effective_at = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = models.PhysicianPrescriptionOrder


class PharmacyEncodedOrderFactory(DjangoModelFactory):
    """Model factory to create [opal.pharmacy.models.PharmacyEncodedOrder][] models."""

    physician_prescription_order = factory.SubFactory(PhysicianPrescriptionOrderFactory)
    quantity = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=0)
    unit = 'mg'
    interval_pattern = 'Q6H'   # Every 6 hours
    interval_duration = ''
    duration = 'D4'  # For a duration of 4 days
    service_start = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    service_end = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())
    priority = 'S'  # Stat priority
    give_code = factory.SubFactory(CodedElementFactory)
    give_amount_maximum = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=20)
    give_amount_minimum = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=0, max_value=19.99)
    give_units = 'mg'
    give_dosage_form = factory.SubFactory(CodedElementFactory)
    provider_administration_instruction = 'Take every 6 hours for 4 days'
    dispense_amount = factory.Faker('pydecimal', left_digits=1, right_digits=0, min_value=0)
    dispense_units = 'mg'
    refills = factory.Faker('pyint')
    refills_remaining = factory.Faker('pyint')
    formulary_status = 'STD'  # standard

    class Meta:
        model = models.PharmacyEncodedOrder


class PharmacyRouteFactory(DjangoModelFactory):
    """Model factory to create [opal.pharmacy.models.PharmacyRoute][] models."""

    pharmacy_encoded_order = factory.SubFactory(PharmacyEncodedOrderFactory)
    route = factory.SubFactory(CodedElementFactory)
    administration_method = factory.SubFactory(CodedElementFactory)

    class Meta:
        model = models.PharmacyRoute


class PharmacyComponentFactory(DjangoModelFactory):
    """Model factory to create [opal.pharmacy.models.PharmacyComponent][] models."""

    pharmacy_encoded_order = factory.SubFactory(PharmacyEncodedOrderFactory)
    component_type = models.ComponentType.ADDITIVE
    component_code = factory.SubFactory(CodedElementFactory)
    component_amount = factory.Faker('pydecimal', left_digits=2, right_digits=3, min_value=0)
    component_units = 'mg'

    class Meta:
        model = models.PharmacyComponent
