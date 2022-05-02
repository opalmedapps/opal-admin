from typing import Type

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from .. import factories
from ..models import Caregiver, CaregiverProfile, ClinicalStaff, User, UserType

UserModel: Type[User] = get_user_model()
pytestmark = pytest.mark.django_db


def test_user_default_type() -> None:
    """User has the default user type set."""
    user = UserModel.objects.create()

    assert user.type == UserModel.base_type
    assert user.type == UserType.CLINICAL_STAFF


def test_user_type_constraint() -> None:
    """User cannot be saved when assigning an invalid user type."""
    user = UserModel.objects.create()
    user.type = 'DOCTOR'

    constraint_name = 'users_user_type_valid'
    # see: https://github.com/pytest-dev/pytest-django/issues/1009
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        user.save()


def test_user_language_constraint() -> None:
    """User cannot be saved when assigning an invalid language."""
    user = UserModel.objects.create()
    user.language = 'DE'

    constraint_name = 'users_user_language_valid'
    # see: https://github.com/pytest-dev/pytest-django/issues/1009
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        user.save()


def test_user_save_existing() -> None:
    """User type is not changed to the default type by save() when changing it on an existing user."""
    user = ClinicalStaff.objects.create()
    assert user.type == UserType.CLINICAL_STAFF

    user.type = UserType.CAREGIVER
    user.save()
    user.refresh_from_db()

    assert user.type == UserType.CAREGIVER


def test_user_objects() -> None:
    """All users are returned by the user manager."""
    factories.User()
    factories.Caregiver()

    assert UserModel.objects.count() == 2


def test_user_phone_number_optional() -> None:
    """User phone number is optional and if not set is stored as an empty string."""
    user = factories.User()
    user.full_clean()

    assert user.phone_number == ''


@pytest.mark.parametrize('phone_number', [
    # min number of digits
    '+1514123',
    # max number of digits
    '+151412345678901',
    # international number
    '+49745812345',
])
def test_user_phone_number_regex(phone_number: str) -> None:
    """Phone number regex handles E.164 format."""
    user = factories.User()
    user.full_clean()

    user.phone_number = phone_number
    user.full_clean()


@pytest.mark.parametrize('phone_number', [
    # not enough number of digits
    '+151412',
    # too many digits
    '+1514123456789012',
    # needs international country code prefix
    '5141234567',
    # country codes don't start with a zero
    '+01234567',
])
def test_user_phone_number_regex_invalid(phone_number: str) -> None:
    """Phone number regex excludes invalid cases."""
    user = factories.User()
    user.full_clean()

    user.phone_number = phone_number

    with assertRaisesMessage(ValidationError, 'phone_number'):  # type: ignore[arg-type]
        user.full_clean()


def test_caregiver_correct_type() -> None:
    """Caregiver has the correct user type set."""
    user = Caregiver.objects.create()

    assert user.type == Caregiver.base_type
    assert user.type == UserType.CAREGIVER


def test_caregiver_objects() -> None:
    """All users with type `CAREGIVER` are returned by the caregiver manager."""
    factories.User()
    caregiver = factories.Caregiver()

    assert Caregiver.objects.count() == 1
    assert Caregiver.objects.first() == caregiver


def test_clinicalstaff_correct_type() -> None:
    """Clinical staff user has the correct user type set."""
    user = ClinicalStaff.objects.create()

    assert user.type == ClinicalStaff.base_type
    assert user.type == UserType.CLINICAL_STAFF


def test_clinicalstaff_objects() -> None:
    """All users with type `CLINICAL_STAFF` are returned by the clinical staff manager."""
    clinical_staff = factories.User()
    factories.Caregiver()

    assert ClinicalStaff.objects.count() == 1
    assert ClinicalStaff.objects.first() == clinical_staff


def test_caregiverprofile_str() -> None:
    """The `str` method returns the name of the associated user."""
    caregiver = factories.Caregiver(first_name='John', last_name='Wayne')

    profile = CaregiverProfile()
    profile.user = caregiver

    assert str(profile) == 'John Wayne'


def test_caregiverprofile_user_limited() -> None:
    """The `CaregiverProfile` needs to be associated with a user of type `Caregiver`."""
    caregiver = factories.Caregiver()
    clinical_staff = factories.User()
    profile = CaregiverProfile(user=clinical_staff)

    with assertRaisesMessage(ValidationError, 'user'):  # type: ignore[arg-type]
        profile.full_clean()

    profile.user = caregiver
    profile.full_clean()


def test_caregiverprofile_cannot_delete_caregiver() -> None:
    """A `Caregiver` cannot be deleted if a `CaregiverProfile` references it."""
    caregiver = factories.Caregiver()

    CaregiverProfile.objects.create(user=caregiver)

    expected_message = (
        "Cannot delete some instances of model 'Caregiver' because they are referenced through "
        + "protected foreign keys: 'CaregiverProfile.user'"
    )

    with assertRaisesMessage(ProtectedError, expected_message):  # type: ignore[arg-type]
        caregiver.delete()


def test_caregiverprofile_legacy_id() -> None:
    """The legacy ID of `CaregiverProfile` needs to be at least 1."""
    caregiver = factories.Caregiver()

    profile = CaregiverProfile(user=caregiver)
    profile.full_clean()

    profile.legacy_id = 0

    expected_message = 'Ensure this value is greater than or equal to 1.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        profile.full_clean()

    profile.legacy_id = 1
    profile.full_clean()
