
from django.core.exceptions import ValidationError
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
    answer.profile = profile
    assert str(answer) == 'first_name last_name - Apple - answer'


def test_security_answer_factory() -> None:
    """Ensure the SecurityAnswer factory is building properly."""
    answer = factories.SecurityAnswer()
    answer.full_clean()
