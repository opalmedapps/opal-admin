from typing import Type

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from .. import factories
from ..models import Caregiver, ClinicalStaff, User, UserType

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
    with assertRaisesMessage(IntegrityError, constraint_name):
        user.save()


def test_user_language_constraint() -> None:
    """User cannot be saved when assigning an invalid language."""
    user = UserModel.objects.create()
    user.language = 'DE'

    constraint_name = 'users_user_language_valid'
    # see: https://github.com/pytest-dev/pytest-django/issues/1009
    with assertRaisesMessage(IntegrityError, constraint_name):
        user.save()


def test_user_save_existing() -> None:
    """User type is not changed to the default type by save() when changing it on an existing user."""
    user = ClinicalStaff.objects.create()
    assert user.type == UserType.CLINICAL_STAFF

    user.type = UserType.CAREGIVER
    user.save()
    user.refresh_from_db()

    assert user.type == UserType.CAREGIVER


def test_user_factory() -> None:
    """The factory for `User` creates a valid user instance."""
    user = factories.User()
    user.full_clean()


def test_user_objects() -> None:
    """All users are returned by the user manager."""
    factories.User()
    factories.Caregiver()

    assert UserModel.objects.count() == 2


def test_user_phone_number_optional() -> None:
    """User phone number is optional and if not set is stored as an empty string."""
    user = factories.User()

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

    user.phone_number = phone_number

    with assertRaisesMessage(ValidationError, 'phone_number'):
        user.full_clean()


@pytest.mark.parametrize('phone_number', [
    # min number of digits
    '+1514123x1',
    # max number of digits
    '+151412345678901x12345',
    # international number
    '+49745812345x0',
    # extension with leading zeros
    '+15141234567x00010',
])
def test_user_phone_number_ext_regex(phone_number: str) -> None:
    """Phone number regex handles extension."""
    user = factories.User()

    user.phone_number = phone_number
    user.full_clean()


@pytest.mark.parametrize('phone_number', [
    # no extension digits
    '+1514123x',
    # too many extension digits
    '+1514123x123456',
    # invalid separator
    '+49745812345ext0',
])
def test_user_phone_number_ext_regex_invalid(phone_number: str) -> None:
    """Phone number regex excludes invalid cases for the extension."""
    user = factories.User()

    user.phone_number = phone_number

    with assertRaisesMessage(ValidationError, 'phone_number'):
        user.full_clean()


def test_caregiver_correct_type() -> None:
    """Caregiver has the correct user type set."""
    user = Caregiver.objects.create()

    assert user.type == Caregiver.base_type
    assert user.type == UserType.CAREGIVER


def test_caregiver_factory() -> None:
    """The factory for `Caregiver` creates a valid instance."""
    caregiver = factories.Caregiver()

    caregiver.full_clean()


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
