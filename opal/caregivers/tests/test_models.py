import datetime

from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from django.db.models.deletion import ProtectedError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.patients import factories as patient_factories
from opal.patients.models import Patient, Relationship, RelationshipType
from opal.users import factories as user_factories
from opal.users.models import Caregiver

from .. import factories
from ..models import CaregiverProfile, RegistrationCode

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


def test_registrationcode_str() -> None:  # pylint: disable-msg=too-many-locals
    """The `str` method returns the registration code of the associated relationship."""
    caregiver = user_factories.Caregiver(first_name='bbb', last_name='222')
    relationshiptype = patient_factories.RelationshipType(name='caregiver', name_fr='Proche aidant')
    relationship = patient_factories.Relationship()
    relationship.patient = patient_factories.Patient(first_name='aaa', last_name='111')
    relationship.caregiver = CaregiverProfile(user=caregiver)
    relationship.type = relationshiptype
    registration_code = factories.RegistrationCode(relationship=relationship)
    assert str(registration_code) == 'Code: code12345678 (Status: NEW)'


def test_registrationcode_factory() -> None:
    """Ensure the Regtistrationcode factory is building properly."""
    registration_code = factories.RegistrationCode()
    registration_code.full_clean()


def test_registrationcode_code_unique() -> None:
    """Ensure the code of registration code is unique."""
    caregiver = Caregiver(first_name='bbb', last_name='222')
    caregiver.save()
    relationshiptype = RelationshipType(
        name='caregiver',
        name_fr='Proche aidant',
        start_age=14,
    )
    relationshiptype.save()
    patient = Patient(
        first_name='aaa',
        last_name='111',
        date_of_birth=datetime.date(1999, 1, 1),
    )
    patient.save()
    profile = CaregiverProfile(user=caregiver)
    profile.save()
    relationship = Relationship(
        patient=patient,
        caregiver=profile,
        type=relationshiptype,
        request_date=datetime.date.today(),
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2020, 5, 1),
    )
    relationship.save()
    RegistrationCode.objects.create(relationship=relationship, code='code12345678')
    with assertRaisesMessage(IntegrityError, "Duplicate entry 'code12345678' for key 'code'"):  # type: ignore[arg-type]
        RegistrationCode.objects.create(relationship=relationship, code='code12345678')


def test_registrationcode_code_length_gt() -> None:
    """Ensure the length of registration code is not greater than 12."""
    expected_message = "Data too long for column 'code' at row 1"
    with assertRaisesMessage(DataError, expected_message):  # type: ignore[arg-type]
        factories.RegistrationCode(code='1234567890111')


def test_registrationcode_email_code_length_gt() -> None:
    """Ensure the length of email verification code is not greater than 6."""
    expected_message = "Data too long for column 'email_verification_code' at row 1"
    with assertRaisesMessage(DataError, expected_message):  # type: ignore[arg-type]
        registration_code = factories.RegistrationCode(email_verification_code='1234567')
        registration_code.clean()


def test_registrationcode_codes_length_lt() -> None:
    """Ensure the length of registration code is not less than 12."""
    registration_code = factories.RegistrationCode(
        code='123456',
        email_verification_code='1234',
    )
    expected_message = '{0}{1}'.format(
        "'Code': ['Code length should be equal to 12.'], ",
        "'Email Verification Code': ['Code length should be equal to 6.']",
    )
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        registration_code.clean()


def test_registrationcode_creation_date() -> None:
    """Ensure the creation date is tody when creating a new registration code."""
    registration_code = factories.RegistrationCode()
    assert str(registration_code.creation_date) == str(datetime.date.today())
