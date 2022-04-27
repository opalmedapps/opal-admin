from typing import Type

from django.contrib.auth import get_user_model
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
