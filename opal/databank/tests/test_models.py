
from django.db import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.patients.factories import Patient

from .. import factories
from ..models import SharedData

pytestmark = pytest.mark.django_db()


def test_databankconsent_factory() -> None:
    """Ensure the `DatabankConsent` factory creates a valid model."""
    databank_consent = factories.DatabankConsent()

    databank_consent.full_clean()


def test_databankconsent_str() -> None:
    """Ensure the `__str__` method is defined for the `DatabankConsent` model."""
    databank_consent = factories.DatabankConsent()
    databank_consent.full_clean()

    assert str(databank_consent) == "Simpson, Bart's Databank Consent"


def test_shareddata_factory() -> None:
    """Ensure the `SharedData` factory creates a valid model."""
    shared_data = factories.SharedData()

    shared_data.full_clean()


def test_shareddata_str() -> None:
    """Ensure the `__str__` method is defined for the `SharedData` model."""
    shared_data = factories.SharedData()
    shared_data.full_clean()

    assert str(shared_data) == f'{shared_data.get_data_type_display()} datum, sent at {shared_data.sent_at}'


def test_sharedata_datatype_constraint() -> None:
    """Ensure the valid choices for the shared data's `type` are validated using a constraint."""
    databank_consent = factories.DatabankConsent()
    shared_data = factories.SharedData.build(databank_consent=databank_consent, data_type='INV')

    constraint_name = 'databank_shareddata_data_type_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):
        shared_data.save()


def test_shareddata_multiple_per_patient() -> None:
    """Ensure a patient (via a DatabankConsent) can have multiple instances of SharedData."""
    patient = Patient()
    databank_consent = factories.DatabankConsent(patient=patient)

    factories.SharedData(databank_consent=databank_consent)
    factories.SharedData(databank_consent=databank_consent)
    factories.SharedData(databank_consent=databank_consent)

    assert SharedData.objects.count() == 3
