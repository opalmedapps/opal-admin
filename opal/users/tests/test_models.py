# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from config.settings.base import ADMIN_GROUP_NAME, ORMS_GROUP_NAME

from .. import factories
from ..models import Caregiver, ClinicalStaff, User, UserType

UserModel: type[User] = get_user_model()
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
    user = factories.User.create()
    user.full_clean()


def test_user_objects() -> None:
    """All users are returned by the user manager."""
    factories.User.create()
    factories.Caregiver.create()

    assert UserModel.objects.count() == 2


def test_user_phone_number_optional() -> None:
    """User phone number is optional and if not set is stored as an empty string."""
    user = factories.User.create()

    assert user.phone_number == ''


@pytest.mark.parametrize(
    'phone_number',
    [
        # required number of digits for CA region
        '+15142345678',
        # can handle local phone numbers
        '5142345678',
        # international number
        '+49745812345',
    ],
)
def test_user_phone_number_regex(phone_number: str) -> None:
    """Phone number regex handles E.164 format."""
    user = factories.User.create()

    user.phone_number = phone_number
    user.full_clean()


@pytest.mark.parametrize(
    'phone_number',
    [
        # min number of digits
        '+15142345678x1',
        # local number
        '5142345678x123',
        # ext.
        '+15142345678 ext. 12345',
        # international number
        '+49745812345x0',
        # extension with leading zeros
        '+15142345678x00010',
    ],
)
def test_user_phone_number_supports_extension(phone_number: str) -> None:
    """Phone number handles extension."""
    user = factories.User.create()

    user.phone_number = phone_number
    user.full_clean()


def test_caregiver_correct_type() -> None:
    """Caregiver has the correct user type set."""
    user = Caregiver.objects.create()

    assert user.type == Caregiver.base_type
    assert user.type == UserType.CAREGIVER


def test_caregiver_factory() -> None:
    """The factory for `Caregiver` creates a valid instance."""
    caregiver = factories.Caregiver.create()

    caregiver.full_clean()


def test_caregiver_objects() -> None:
    """All users with type `CAREGIVER` are returned by the caregiver manager."""
    factories.User.create()
    caregiver = factories.Caregiver.create()

    assert Caregiver.objects.count() == 1
    assert Caregiver.objects.first() == caregiver


def test_clinicalstaff_correct_type() -> None:
    """Clinical staff user has the correct user type set."""
    user = ClinicalStaff.objects.create()

    assert user.type == ClinicalStaff.base_type
    assert user.type == UserType.CLINICAL_STAFF


def test_clinicalstaff_objects() -> None:
    """All users with type `CLINICAL_STAFF` are returned by the clinical staff manager."""
    clinical_staff = factories.User.create()
    factories.Caregiver.create()

    assert ClinicalStaff.objects.count() == 1
    assert ClinicalStaff.objects.first() == clinical_staff


def test_user_admin_group_add_signal() -> None:
    """User properties `is_staff` and `is_superuser` are activated when added to the defined admin Group ."""
    clinical_staff = factories.User.create()
    # create an admin group
    admingroup = factories.GroupFactory.create(name=ADMIN_GROUP_NAME)

    # add user to the created admin group
    clinical_staff.groups.add(admingroup)

    # assert that staff and superuser properties are activated
    assert clinical_staff.is_superuser
    assert clinical_staff.is_staff


def test_user_admin_group_remove_signal() -> None:
    """User properties `is_staff` and `is_superuser` are deactivated when removed from the defined admin group."""
    # create a user
    clinical_staff = factories.User.create(is_superuser=True, is_staff=True)
    # activate superuser and staff properties
    # create admin group
    admingroup = factories.GroupFactory.create(name=ADMIN_GROUP_NAME)

    # add user to admin group
    clinical_staff.groups.add(admingroup)
    # remove user from admin group
    clinical_staff.groups.remove(admingroup)

    # assert that properties are deactivated
    assert not clinical_staff.is_superuser
    assert not clinical_staff.is_staff


def test_user_group_add_not_change_status() -> None:
    """User properties `is_staff` and `is_superuser` are not changed when another group is added."""
    # create a user
    clinical_staff = factories.User.create(is_superuser=True, is_staff=True)
    # create a group
    group = factories.GroupFactory.create(name=ORMS_GROUP_NAME)

    # add user to admin group
    clinical_staff.groups.add(group)

    # assert that properties are deactivated
    assert clinical_staff.is_superuser
    assert clinical_staff.is_staff


def test_user_group_remove_not_change_status() -> None:
    """User properties `is_staff` and `is_superuser` are not changed when another group is removed."""
    # create a user
    clinical_staff = factories.User.create(is_superuser=True, is_staff=True)
    # create a group
    group = factories.GroupFactory.create(name=ORMS_GROUP_NAME)

    # add user to non-admin group
    clinical_staff.groups.add(group)
    clinical_staff.groups.remove(group)

    # assert that properties are not affected
    assert clinical_staff.is_superuser
    assert clinical_staff.is_staff


def test_user_nonclinical_user_add_not_change_status() -> None:
    """User properties `is_staff` and `is_superuser` are unaffected when nonclinical user is added to admingroup."""
    # create a user
    clinical_staff = factories.Caregiver.create()
    # create a group
    admingroup = factories.GroupFactory.create(name=ADMIN_GROUP_NAME)

    # add user to admin group
    clinical_staff.groups.add(admingroup)

    # assert that properties are not affected
    assert not clinical_staff.is_superuser
    assert not clinical_staff.is_staff


def test_user_nonclinical_user_remove_not_change_status() -> None:
    """User properties `is_staff` and `is_superuser` are unaffected when nonclinical user is removed from admingroup."""
    # create a user
    clinical_staff = factories.Caregiver.create(is_staff=True, is_superuser=True)
    # create a group
    admingroup = factories.GroupFactory.create(name=ADMIN_GROUP_NAME)

    # add user to admin group
    clinical_staff.groups.add(admingroup)
    clinical_staff.groups.remove(admingroup)

    # assert that properties are not affected
    assert clinical_staff.is_superuser
    assert clinical_staff.is_staff


def test_user_group_remove_add_multiple_groups() -> None:
    """User properties `is_staff` and `is_superuser` changed when multiple groups are added and removed."""
    # create a user
    clinical_staff = factories.User.create()
    # create a group
    admingroup = factories.GroupFactory.create(name=ADMIN_GROUP_NAME)
    ormsgroup = factories.GroupFactory.create(name=ORMS_GROUP_NAME)
    testgroup = factories.GroupFactory.create(name='test_group')

    clinical_staff.groups.add(admingroup)
    clinical_staff.groups.add(ormsgroup)
    clinical_staff.groups.add(testgroup)

    # assert that properties are activated
    assert clinical_staff.is_superuser
    assert clinical_staff.is_staff

    clinical_staff.groups.remove(ormsgroup)
    clinical_staff.groups.remove(testgroup)

    # assert that properties are activated
    assert clinical_staff.is_superuser
    assert clinical_staff.is_staff

    clinical_staff.groups.add(testgroup)
    clinical_staff.groups.remove(admingroup)

    # assert that properties are deactivated
    assert not clinical_staff.is_superuser
    assert not clinical_staff.is_staff
