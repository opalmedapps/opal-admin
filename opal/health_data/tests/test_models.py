from django.core.exceptions import ValidationError
from django.db import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from .. import factories
from ..models import QuantitySample, QuantitySampleType

pytestmark = pytest.mark.django_db()


def test_healthdatastore_factory() -> None:
    """Ensure the `HealthDataStore` factory creates a valid model."""
    data_store = factories.HealthDataStore()

    data_store.full_clean()


def test_healthdatastore_str() -> None:
    """Ensure the `__str__` method is defined for the `HealthDataStore` model."""
    data_store = factories.HealthDataStore.build()

    assert str(data_store) == 'Health Data Store for Bart Simpson'


def test_healthdatastore_unique_per_patient() -> None:
    """Ensure a patient can only have one `HealthDataStore`."""
    data_store = factories.HealthDataStore()
    data_store2 = factories.HealthDataStore()

    # the factory gets the existing one by default
    assert data_store == data_store2

    # pretend this is a new instance
    data_store2.id = None

    constraint_name = 'health_data_healthdatastore_unique_patient'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        data_store2.save()


def test_quantitysample_factory() -> None:
    """Ensure the `QuantitySample` factory creates a valid model."""
    sample = factories.QuantitySample()

    sample.full_clean()


def test_quantitysample_str_no_type() -> None:
    """Ensure the `__str__` method is defined for the `QuantitySample` model and can handle no type set."""
    sample = QuantitySample()

    assert str(sample) == 'QuantitySample object (None)'


def test_quantitysample_str() -> None:
    """Ensure the `__str__` method is defined for the `QuantitySample` model."""
    sample = factories.QuantitySample(type=QuantitySampleType.HEART_RATE, value=60)
    sample.full_clean()

    assert str(sample) == '60 bpm'


@pytest.mark.parametrize('sample_type', QuantitySampleType.values)
def test_quantitysampletype_unit_defined(sample_type: str) -> None:
    """Ensure there exists a `Unit` for each unit referenced in the `QuantitySampleTypes`."""
    sample = QuantitySample(type=sample_type, value=12.34)

    # separate value and unit
    text = str(sample).split(' ')

    assert len(text) == 2
    assert text[0] == '12.34'
    # ensure that there is a unit
    assert text[1]


def test_quantitysample_type_constraint() -> None:
    """Ensure the valid choices for the sample's `type` are validated using a constraint."""
    data_store = factories.HealthDataStore()
    sample = factories.QuantitySample.build(data_store=data_store, type='INV')

    constraint_name = 'health_data_quantitysample_type_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        sample.save()


def test_quantitysample_source_constraint() -> None:
    """Ensure the valid choices for the sample's `source` are validated using a constraint."""
    data_store = factories.HealthDataStore()
    sample = factories.QuantitySample.build(data_store=data_store, source='I')

    constraint_name = 'health_data_quantitysample_source_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        sample.save()


def test_quantitysample_new_can_save() -> None:
    """Ensure a new instance can be saved."""
    data_store = factories.HealthDataStore()
    sample = factories.QuantitySample.build(data_store=data_store)

    sample.save()


def test_quantitysample_existing_cannot_save() -> None:
    """Ensure an existing instance cannot be saved."""
    sample = factories.QuantitySample()

    with pytest.raises(ValidationError, match='Cannot change an existing instance of Quantity Sample'):
        sample.save()
