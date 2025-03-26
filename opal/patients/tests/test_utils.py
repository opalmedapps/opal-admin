"""App patient utils test functions."""
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.caregivers import models as caregiver_models
from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.patients.factories import Patient
from opal.users.factories import User

from ..utils import insert_security_answers, update_caregiver, update_patient_legacy_id, update_registration_code_status

pytestmark = pytest.mark.django_db


def test_update_registration_code_status_success() -> None:
    """Test get registration code and update its status success."""
    registration_code = RegistrationCode(status=caregiver_models.RegistrationCodeStatus.NEW)
    update_registration_code_status(registration_code)
    registration_code.refresh_from_db()
    assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED


def test_update_patient_legacy_id_valid() -> None:
    """Test update patient legacy id with valid value."""
    patient = Patient()
    legacy_id = patient.legacy_id + 1
    update_patient_legacy_id(patient, legacy_id)
    patient.refresh_from_db()
    assert patient.legacy_id == legacy_id


def test_update_patient_legacy_id_invalid() -> None:
    """Test update patient legacy id with invalid value."""
    patient = Patient()
    legacy_id = 0
    expected_message = "'legacy_id': ['Ensure this value is greater than or equal to 1.']"
    with assertRaisesMessage(
        ValidationError,  # type: ignore[arg-type]
        expected_message,
    ):
        update_patient_legacy_id(patient, legacy_id)


def test_update_caregiver_success() -> None:
    """Test update caregiver information success."""
    phone_number1 = '+15141112222'
    phone_number2 = '+15141112223'
    language1 = 'en'
    language2 = 'fr'
    user = User(phone_number=phone_number1, language=language1)
    info: dict = {
        'user': {
            'language': language2,
            'phone_number': phone_number2,
        },
    }
    update_caregiver(user, info)
    user.refresh_from_db()
    assert user.language == language2
    assert user.phone_number == phone_number2


def test_update_caregiver_failure() -> None:
    """Test update caregiver information failure."""
    phone_number1 = '+15141112222'
    phone_number2 = '11111112223'
    language1 = 'en'
    language2 = 'fr'
    user = User(phone_number=phone_number1, language=language1)
    info: dict = {
        'user': {
            'language': language2,
            'phone_number': phone_number2,
        },
    }
    expected_message = "{'phone_number': ['Enter a valid value.']}"
    with assertRaisesMessage(
        ValidationError,  # type: ignore[arg-type]
        expected_message,
    ):
        update_caregiver(user, info)


def test_insert_security_answers_success() -> None:
    """Test insert security answers success."""
    caregiver = CaregiverProfile()
    security_answers = [
        {
            'question': 'correct?',
            'answer': 'yes',
        },
        {
            'question': 'correct?',
            'answer': 'maybe',
        },
    ]
    insert_security_answers(caregiver, security_answers)
    security_answers_objs = caregiver_models.SecurityAnswer.objects.all()
    assert len(security_answers_objs) == 2


def test_insert_security_answers_failure() -> None:
    """Test insert security answers failure."""
    caregiver = CaregiverProfile()
    security_answers = [
        {
            'question': None,
            'answer': 'yes',
        },
        {
            'question': 'correct?',
            'answer': 'maybe',
        },
    ]
    expected_message = "Column 'question' cannot be null"
    with assertRaisesMessage(
        IntegrityError,  # type: ignore[arg-type]
        expected_message,
    ):
        insert_security_answers(caregiver, security_answers)
