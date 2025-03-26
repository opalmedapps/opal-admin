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
    assert str(question) == 'question_one question_un'


def test_security_question_factory() -> None:
    """Ensure the SecurityQuestion factory is building properly."""
    question = factories.SecurityQuestion()
    question.full_clean()


def test_security_question_active() -> None:
    """Security Question is active as default."""
    question = factories.SecurityQuestion()
    assert question.is_active


def test_security_question_clean_valid_dates() -> None:
    """Ensure that the date is valid if created_at is earlier than updated_at."""
    question = factories.SecurityQuestion(created_at='2022-06-06', updated_at='2022-06-07')
    question.clean()


def test_security_question_clean_invalid_dates() -> None:
    """Ensure that the date is invalid if created_at is later than updated_at."""
    question = factories.SecurityQuestion()
    question.created_at = datetime.date(2022, 6, 8)
    question.updated_at = datetime.date(2022, 6, 6)

    expected_message = 'Creation date should be earlier than last updated date.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        question.clean()


def test_security_question_dates_constraint() -> None:
    """Ensure that the date cannot be saved if created_at is later than updated_at."""
    question = factories.SecurityQuestion()
    question.created_at = datetime.date(2022, 6, 8)
    question.updated_at = datetime.date(2022, 6, 6)

    constraint_name = 'caregivers_securityquestion_date_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        question.save()


def test_security_answer_str() -> None:
    """The `str` method returns the name of the user and the answer of security answer."""
    answer = factories.SecurityAnswer()
    caregiver = user_factories.Caregiver(first_name='first_name', last_name='last_name')
    profile = CaregiverProfile()
    profile.user = caregiver
    answer.profile = profile
    assert str(answer) == 'first_name last_name - question_one question_un'


def test_security_answer_factory() -> None:
    """Ensure the SecurityAnswer factory is building properly."""
    answer = factories.SecurityAnswer()
    answer.full_clean()


def test_security_answer_clean_valid_dates() -> None:
    """Ensure that the date is valid if created_at is earlier than updated_at."""
    answer = factories.SecurityAnswer(created_at='2022-06-06', updated_at='2022-06-07')
    answer.clean()


def test_security_answer_clean_invalid_dates() -> None:
    """Ensure that the date is invalid if created_at is later than updated_at."""
    answer = factories.SecurityAnswer()
    answer.created_at = datetime.date(2022, 6, 8)
    answer.updated_at = datetime.date(2022, 6, 6)

    expected_message = 'Creation date should be earlier than last updated date.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        answer.clean()


def test_security_answer_invalid_dates_constraint() -> None:
    """Ensure that the date cannot be saved if created_at is later than updated_at."""
    answer = factories.SecurityAnswer()
    answer.created_at = datetime.date(2022, 6, 8)
    answer.updated_at = datetime.date(2022, 6, 6)

    constraint_name = 'caregivers_securityanswer_date_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        answer.save()
