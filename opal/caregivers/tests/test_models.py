import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.db.utils import DataError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.users import factories as user_factories

from .. import factories
from ..models import CaregiverProfile, Device, DeviceType, EmailVerification

pytestmark = pytest.mark.django_db


def test_caregiverprofile_factory() -> None:
    """The Caregiver Profile factory is building a valid model."""
    profile = factories.CaregiverProfile()
    profile.full_clean()


def test_caregiverprofile_factory_multiple() -> None:
    """The Caregiver Profile factory can build multiple default model instances."""
    profile = factories.CaregiverProfile()
    profile2 = factories.CaregiverProfile()

    assert profile.user != profile2.user
    assert profile.uuid != profile2.uuid


def test_caregiverprofile_uuid_unique() -> None:
    """Ensure that the field uuid of carigaver is unique."""
    profile = factories.CaregiverProfile()
    profile2 = factories.CaregiverProfile()
    profile.uuid = profile2.uuid
    message = 'Caregiver Profile with this UUID already exists.'
    with assertRaisesMessage(ValidationError, message):
        profile.full_clean()


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

    with assertRaisesMessage(ValidationError, 'user'):
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

    with assertRaisesMessage(ProtectedError, expected_message):
        caregiver.delete()


def test_caregiverprofile_legacy_id() -> None:
    """The legacy ID of `CaregiverProfile` needs to be at least 1."""
    caregiver = user_factories.Caregiver()

    profile = CaregiverProfile(user=caregiver)
    profile.full_clean()

    profile.legacy_id = 0

    expected_message = 'Ensure this value is greater than or equal to 1.'
    with assertRaisesMessage(ValidationError, expected_message):
        profile.full_clean()

    profile.legacy_id = 1
    profile.full_clean()


def test_caregiverprofile_legacy_id_unique() -> None:
    """Ensure that creating a second `CaregiverProfile` with an existing `legacy_id` raises an `IntegrityError`."""
    factories.CaregiverProfile(legacy_id=1)

    message = "Duplicate entry '1' for key"

    with assertRaisesMessage(IntegrityError, message):
        factories.CaregiverProfile(legacy_id=1)


def test_caregiverprofile_non_existing_legacy_id() -> None:
    """Ensure that multiple `CaregiverProfiles` with a non-existing legacy_id does not raise a `ValidationError`."""
    factories.CaregiverProfile(legacy_id=None)
    factories.CaregiverProfile(legacy_id=None)

    assert CaregiverProfile.objects.count() == 2


def test_security_question_str() -> None:
    """The `str` method returns the name of the security_question."""
    question = factories.SecurityQuestion()
    assert str(question) == 'Apple'


def test_security_question_factory() -> None:
    """Ensure the SecurityQuestion factory is building properly."""
    question = factories.SecurityQuestion()
    question.full_clean()


def test_security_question_factory_multiple() -> None:
    """Ensure the SecurityQuestion factory can build multiple default model instances."""
    question = factories.SecurityQuestion()
    question2 = factories.SecurityQuestion()

    assert question != question2


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


def test_security_answer_factory_multiple() -> None:
    """Ensure the SecurityAnswer factory can build multiple default model instances."""
    answer = factories.SecurityAnswer()
    answer2 = factories.SecurityAnswer()

    assert answer != answer2
    assert answer.user != answer2.user


def test_device_str() -> None:
    """The `str` method returns the device_id and device type."""
    device = factories.Device(device_id='1a2b3c', type=DeviceType.ANDROID)
    assert str(device) == '1a2b3c (AND)'


def test_device_factory() -> None:
    """Ensure the Device factory is building properly."""
    device = factories.Device()
    device.full_clean()


def test_device_factory_multiple() -> None:
    """Ensure the Device factory can build multiple default model instances."""
    device1 = factories.Device()
    device2 = factories.Device()

    assert device1.device_id != device2.device_id


def test_device_untrusted_default() -> None:
    """Ensure that a Device is untrusted by default."""
    device = Device()
    assert not device.is_trusted


def test_device_same_caregiver_same_device() -> None:
    """Ensure that a Device's caregiver_id and device_id combination is unique."""
    caregiver = factories.CaregiverProfile(id=1)
    factories.Device(caregiver=caregiver, device_id='1a2b3c')

    expected_message = "Duplicate entry '1-1a2b3c' for key 'caregivers_device_unique_caregiver_device'"
    with assertRaisesMessage(IntegrityError, expected_message):
        factories.Device(caregiver=caregiver, device_id='1a2b3c')


def test_device_diff_caregivers_same_device() -> None:
    """Ensure that the unique caregiver_id + device_id doesn't prevent two caregivers from sharing a device."""
    caregiver1 = factories.CaregiverProfile()
    caregiver2 = factories.CaregiverProfile()
    factories.Device(caregiver=caregiver1, device_id='1a2b3c')
    factories.Device(caregiver=caregiver2, device_id='1a2b3c')


def test_device_same_caregiver_diff_devices() -> None:
    """Ensure that the unique caregiver_id + device_id doesn't prevent a caregiver from having several devices."""
    caregiver = factories.CaregiverProfile()
    factories.Device(caregiver=caregiver, device_id='1a2b3c')
    factories.Device(caregiver=caregiver, device_id='a1b2c3')


def test_device_push_token_length() -> None:
    """Ensure a device push token can't be greater than 256 characters long."""
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(caregiver=caregiver)
    device.push_token = ''.join('a' for _ in range(260))
    with assertRaisesMessage(DataError, "Data too long for column 'push_token' at row 1"):
        device.save()


def test_device_modified_datatype() -> None:
    """Ensure the device modified field is automatically generated and is of the correct type."""
    caregiver = factories.CaregiverProfile(id=1)
    device = factories.Device(caregiver=caregiver, device_id='1a2b3c')
    assert isinstance(device.modified, datetime.datetime)


def test_registrationcode_str() -> None:  # pylint: disable-msg=too-many-locals
    """The `str` method returns the registration code and status."""
    registration_code = factories.RegistrationCode()
    assert str(registration_code) == 'Code: code12345678 (Status: NEW)'


def test_registrationcode_factory() -> None:
    """Ensure the Regtistrationcode factory is building properly."""
    registration_code = factories.RegistrationCode()
    registration_code.full_clean()


def test_registrationcode_factory_multiple() -> None:
    """Ensure the Regtistrationcode factory can build multiple default model instances."""
    code = factories.RegistrationCode()
    code2 = factories.RegistrationCode(code='test')

    assert code != code2
    assert code.relationship != code2.relationship


def test_registrationcode_code_unique() -> None:
    """Ensure the code of registration code is unique."""
    registration_code = factories.RegistrationCode()
    with assertRaisesMessage(IntegrityError, "Duplicate entry 'code12345678' for key 'code'"):
        factories.RegistrationCode(relationship=registration_code.relationship)


def test_registrationcode_code_length_gt_max() -> None:
    """Ensure the length of registration code is not greater than 12."""
    registration_code = factories.RegistrationCode()
    registration_code.code = 'code1234567890'
    expected_message = "'code': ['Ensure this value has at most 12 characters (it has 14).']"
    with assertRaisesMessage(ValidationError, expected_message):
        registration_code.clean_fields()


def test_registrationcode_codes_length_lt_min() -> None:
    """Ensure the length of registration code is not less than 12."""
    registration_code = factories.RegistrationCode(code='123456')
    expected_message = "'code': ['Ensure this value has at least 12 characters (it has 6).']"
    with assertRaisesMessage(ValidationError, expected_message):
        registration_code.clean_fields()


def test_registrationcode_creation_date_is_today() -> None:
    """Ensure the creation date  is today when creating a new registration code."""
    registration_code = factories.RegistrationCode()
    assert str(registration_code.created_at.date()) == str(datetime.date.today())


class TestEmailVerification:
    """A class is used to test Model EmailVerification."""

    def test_model_str(self) -> None:
        """The `str` method returns the email verification code and status."""
        email_verification = EmailVerification(email='opal@muhc.mcgill.ca', is_verified=True)
        assert str(email_verification) == 'Email: opal@muhc.mcgill.ca (Verified: True)'

    def test_factory(self) -> None:
        """Ensure the EmailVerification factory is building properly."""
        email_verification = factories.EmailVerification()
        email_verification.full_clean()

    def test_default_email_not_verified(self) -> None:
        """Ensure the email is not verified as default."""
        email_verification = EmailVerification()
        assert email_verification.is_verified is False

    def test_email_code_too_long(self) -> None:
        """Ensure the length of email verification code is not greater than 6."""
        email_verification = factories.EmailVerification()
        email_verification.code = '1234567'
        expected_message = "'code': ['Ensure this value has at most 6 characters (it has 7).']"
        with assertRaisesMessage(ValidationError, expected_message):
            email_verification.clean_fields()

    def test_email_code_too_short(self) -> None:
        """Ensure the length of email verification code is not less than 6."""
        email_verification = factories.EmailVerification()
        email_verification.code = '1234'
        expected_message = "'code': ['Ensure this value has at least 6 characters (it has 4).'"
        with assertRaisesMessage(ValidationError, expected_message):
            email_verification.clean_fields()

    def test_email_not_empty(self) -> None:
        """Ensure the field email is not empty."""
        email_verification = factories.EmailVerification()
        email_verification.email = ''
        expected_message = "'email': ['This field cannot be blank.']"
        with assertRaisesMessage(ValidationError, expected_message):
            email_verification.clean_fields()
