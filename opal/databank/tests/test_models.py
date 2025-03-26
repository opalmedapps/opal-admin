
from django.core.exceptions import ValidationError
from django.db import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.patients.factories import Patient

from .. import factories
from ..models import SharedData

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


def test_databankconsent_factory() -> None:
    """Ensure the `DatabankConsent` factory creates a valid model."""
    databank_consent = factories.DatabankConsent()

    databank_consent.full_clean()


def test_databankconsent_str() -> None:
    """Ensure the `__str__` method is defined for the `DatabankConsent` model."""
    databank_consent = factories.DatabankConsent()
    databank_consent.full_clean()

    assert str(databank_consent) == "Simpson, Marge's Databank Consent"


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


def test_guid_generation_missing_patient_legacy_id() -> None:
    """Test Validation error if patient missing legacy id."""
    consenting_patient = Patient(legacy_id=None)
    databank_consent = factories.DatabankConsent(patient=consenting_patient)
    with assertRaisesMessage(ValidationError, "Can't generate a GUID for a patient who is missing their legacy_id."):
        databank_consent.full_clean()


def test_guid_successful_generation(databank_consent_questionnaire_and_response: dict) -> None:
    """Test the guid is created properly if all fields exist."""
    legacy_questionnaire_patient = databank_consent_questionnaire_and_response['patient']
    django_patient = Patient(legacy_id=legacy_questionnaire_patient.external_id)
    print(django_patient)
    databank_consent = factories.DatabankConsent(patient=django_patient)
    databank_consent.full_clean()
    print(databank_consent.guid)
    assert 1 == 0


def test_clean_guid_middle_name_question_fail() -> None:
    """Test the middle name cleaning raises ValidationError for missing question from QuestionnaireDB."""


def test_clean_guid_city_of_birth_question_fail() -> None:
    """Test the city of birth cleaning raises ValidationError for missing question from QuestionnaireDB."""


def test_clean_guid_city_of_birth_answer_fail() -> None:
    """Test the city of birth cleaning raises ValidationError for missing answer from QuestionnaireDB."""
