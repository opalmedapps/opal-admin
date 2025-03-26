import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.users import factories as user_factories

from .. import factories
from ..models import CaregiverProfile

pytestmark = pytest.mark.django_db


def test_caregiverprofile_str() -> None:
    """The `str` method returns the name of the associated user."""
    caregiver = user_factories.Caregiver(first_name='John', last_name='Wayne')

    profile = CaregiverProfile()
    profile.user = caregiver

    assert str(profile) == 'John Wayne'


def test_caregiverprofile_user_limited() -> None:
    """The `CaregiverProfile` needs to be associated with a user of type `Caregiver`."""
    caregiver = user_factories.Caregiver()
    clinical_staff = user_factories.User()
    profile = CaregiverProfile(user=clinical_staff)

    with assertRaisesMessage(ValidationError, 'user'):  # type: ignore[arg-type]
        profile.full_clean()

    profile.user = caregiver
    profile.full_clean()


def test_caregiverprofile_cannot_delete_caregiver() -> None:
    """A `Caregiver` cannot be deleted if a `CaregiverProfile` references it."""
    caregiver = user_factories.Caregiver()

    CaregiverProfile.objects.create(user=caregiver)

    expected_message = (
        "Cannot delete some instances of model 'Caregiver' because they are referenced through "
        + "protected foreign keys: 'CaregiverProfile.user'"
    )

    with assertRaisesMessage(ProtectedError, expected_message):  # type: ignore[arg-type]
        caregiver.delete()


def test_caregiverprofile_legacy_id() -> None:
    """The legacy ID of `CaregiverProfile` needs to be at least 1."""
    caregiver = user_factories.Caregiver()

    profile = CaregiverProfile(user=caregiver)
    profile.full_clean()

    profile.legacy_id = 0

    expected_message = 'Ensure this value is greater than or equal to 1.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        profile.full_clean()

    profile.legacy_id = 1
    profile.full_clean()


def test_security_question_str() -> None:
    """The `str` method returns the name of the security_question."""
    question = factories.SecurityQuestion()
    assert str(question) == 'Apple'


def test_security_question_factory() -> None:
    """Ensure the SecurityQuestion factory is building properly."""
    question = factories.SecurityQuestion()
    question.full_clean()


def test_security_question_active() -> None:
    """Security Question is active as default."""
    question = factories.SecurityQuestion()
    assert question.is_active


def test_security_answer_str() -> None:
    """The `str` method returns the name of the user and the answer of security answer."""
    answer = factories.SecurityAnswer()
    caregiver = user_factories.Caregiver(first_name='first_name', last_name='last_name')
    profile = CaregiverProfile()
    profile.user = caregiver
    answer.user = profile
    assert str(answer) == 'Apple'


def test_security_answer_factory() -> None:
    """Ensure the SecurityAnswer factory is building properly."""
    answer = factories.SecurityAnswer()
    answer.full_clean()


def test_registrationcode_str() -> None:  # pylint: disable-msg=too-many-locals
    """The `str` method returns the registration code and status."""
    registration_code = factories.RegistrationCode()
    assert str(registration_code) == 'Code: code12345678 (Status: NEW)'


def test_registrationcode_factory() -> None:
    """Ensure the Regtistrationcode factory is building properly."""
    registration_code = factories.RegistrationCode()
    registration_code.full_clean()


def test_registrationcode_code_unique() -> None:
    """Ensure the code of registration code is unique."""
    registration_code = factories.RegistrationCode()
    with assertRaisesMessage(IntegrityError, "Duplicate entry 'code12345678' for key 'code'"):  # type: ignore[arg-type]
        factories.RegistrationCode(relationship=registration_code.relationship)


def test_registrationcode_code_length_gt_max() -> None:
    """Ensure the length of registration code is not greater than 12."""
    registration_code = factories.RegistrationCode()
    registration_code.code = 'code1234567890'
    expected_message = "'code': ['Ensure this value has at most 12 characters (it has 14).']"
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        registration_code.clean_fields()


def test_registrationcode_email_code_too_long() -> None:
    """Ensure the length of email verification code is not greater than 6."""
    registration_code = factories.RegistrationCode()
    registration_code.email_verification_code = '1234567'
    expected_message = "'email_verification_code': ['Ensure this value has at most 6 characters (it has 7).']"
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        registration_code.clean_fields()


def test_registrationcode_codes_length_lt_min() -> None:
    """Ensure the length of registration code is not less than 12."""
    registration_code = factories.RegistrationCode(
        code='123456',
        email_verification_code='1234',
    )
    expected_message = '{0}{1}'.format(
        "'code': ['Ensure this value has at least 12 characters (it has 6).'], ",
        "'email_verification_code': ['Ensure this value has at least 6 characters (it has 4).'",
    )
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        registration_code.clean_fields()


def test_registrationcode_creation_date_is_today() -> None:
    """Ensure the creation date is tody when creating a new registration code."""
    registration_code = factories.RegistrationCode()
    assert str(registration_code.creation_date) == str(datetime.date.today())
