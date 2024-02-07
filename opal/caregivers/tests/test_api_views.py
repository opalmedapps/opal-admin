"""Test module for registration api endpoints."""
import copy
import datetime as dt
from datetime import datetime
from hashlib import sha512
from http import HTTPStatus
from typing import Any

from django.core import mail
from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factories
from opal.caregivers import models as caregiver_models
from opal.patients import factories as patient_factories
from opal.patients.factories import Relationship
from opal.users import factories as user_factories
from opal.users.models import Caregiver, User


def test_get_caregiver_patient_list_unauthenticated_unauthorized(api_client: APIClient, user: User) -> None:
    """The patient list endpoint rejects unauthenticated and unauthorized requests."""
    url = reverse('api:caregivers-patient-list')

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'


def test_get_caregiver_patient_list_missing_user_id_header(api_client: APIClient, listener_user: User) -> None:
    """Test patient list endpoint to return a bad request if the `Appuserid` header is missing."""
    api_client.force_authenticate(user=listener_user)

    response = api_client.get(reverse('api:caregivers-patient-list'))

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_caregiver_patient_list_no_patient(api_client: APIClient, listener_user: User) -> None:
    """Test patient list endpoint to return an empty list if there is no relationship."""
    api_client.force_login(user=listener_user)
    caregiver = caregiver_factories.Caregiver()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)

    response = api_client.get(reverse('api:caregivers-patient-list'))

    assert response.status_code == HTTPStatus.OK
    assert not response.data


def test_get_caregiver_patient_list_patient_id(api_client: APIClient, listener_user: User) -> None:
    """Test patient list endpoint to return a list of patients with the correct patient_id and relationship type."""
    api_client.force_login(user=listener_user)
    relationship_type = patient_factories.RelationshipType(name='Mother')
    relationship = patient_factories.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)

    response = api_client.get(reverse('api:caregivers-patient-list'))

    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 1
    assert relationship.type_id == response.data[0]['relationship_type']['id']
    assert str(relationship.patient.uuid) == response.data[0]['patient_uuid']


def test_get_caregiver_patient_list_fields(api_client: APIClient, listener_user: User) -> None:
    """Test patient list endpoint to return a list of patients with the correct response fields."""
    api_client.force_login(user=listener_user)
    relationship_type = patient_factories.RelationshipType(name='Mother')
    patient_factories.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)

    response = api_client.get(reverse('api:caregivers-patient-list'))

    data_fields = [
        'patient_uuid',
        'patient_legacy_id',
        'first_name', 'last_name',
        'status',
        'relationship_type',
        'data_access',
    ]
    for data_field in data_fields:
        assert data_field in response.data[0]

    relationship_type_fields = ['id', 'name', 'can_answer_questionnaire', 'role_type']
    for relationship_type_field in relationship_type_fields:
        assert relationship_type_field in response.data[0]['relationship_type']


def test_caregiver_profile_unauthenticated_unauthorized(api_client: APIClient, user: User) -> None:
    """The caregiver profile endpoint rejects unauthenticated and unauthorized requests."""
    url = reverse('api:caregivers-profile')

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'


def test_caregiver_profile(api_client: APIClient, listener_user: User) -> None:
    """The caregiver's profile is returned."""
    caregiver_profile = caregiver_factories.CaregiverProfile(user__username='johnwaynedabest')

    api_client.force_login(user=listener_user)
    api_client.credentials(HTTP_APPUSERID=caregiver_profile.user.username)
    response = api_client.get(reverse('api:caregivers-profile'))

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    expected_data = ['uuid', 'first_name', 'last_name', 'language', 'phone_number', 'username', 'devices', 'legacy_id']
    assert list(data.keys()) == expected_data
    assert data['username'] == 'johnwaynedabest'
    assert not data['devices']


def test_caregiver_profile_not_found(api_client: APIClient, listener_user: User) -> None:
    """A 404 is returned if the caregiver does not exist."""
    api_client.force_login(user=listener_user)
    api_client.credentials(HTTP_APPUSERID='johnwaynedabest')
    response = api_client.get(reverse('api:caregivers-profile'))

    assert response.status_code == HTTPStatus.NOT_FOUND
    # ensure that the response contains JSON
    response.json()


def test_caregiver_profile_missing_header(api_client: APIClient, listener_user: User) -> None:
    """An error is returned if the `Appuserid` header is missing."""
    api_client.force_login(user=listener_user)
    response = api_client.get(reverse('api:caregivers-profile'))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = response.json()

    assert 'detail' in data


def test_registration_encryption_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    registration_listener_user: User,
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    url = reverse('api:registration-by-hash', kwargs={'hash': 'some-hash'})

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(registration_listener_user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK


def test_registration_encryption_return_values(api_client: APIClient, admin_user: User) -> None:
    """Test status code and registration code value."""
    api_client.force_login(user=admin_user)
    registration_code = caregiver_factories.RegistrationCode()
    patient_factories.HospitalPatient(patient=registration_code.relationship.patient)
    request_hash = sha512(registration_code.code.encode()).hexdigest()

    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': request_hash}))

    assert response.status_code == HTTPStatus.OK
    assert response.data['code'] == registration_code.code


def test_registration_encryption_invalid_hash(api_client: APIClient, admin_user: User) -> None:
    """Return 404 if the hash is invalid."""
    api_client.force_login(user=admin_user)
    registration_code = caregiver_factories.RegistrationCode()
    patient_factories.HospitalPatient(patient=registration_code.relationship.patient)
    invalid_hash = sha512('badcode'.encode()).hexdigest()

    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': invalid_hash}))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_device_unauthenticated_unauthorized(api_client: APIClient, user: User) -> None:
    """Test that unauthenticated and unauthorized requests get rejected."""
    url = reverse('api:devices-update-or-create', kwargs={'device_id': '123456'})

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'


def test_device_put_create(api_client: APIClient, listener_user: User) -> None:
    """Test creating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)

    device_id = '3840166df22af52b5ac8fe757371c314d281ad3a83f1dd5f2e4df865'

    data = {
        'device_id': device_id,
        'type': caregiver_models.DeviceType.IOS,
        'caregiver': caregiver.id,
        'is_trusted': False,
        'push_token': '2803df883164a7c8f12126f802a7d5fd08c361bca1e7b7a0acf88d361be54c4cc547b5a6c13141ecc5d7e',
    }

    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device_id},
        ),
        data=data,
    )

    assert response.status_code == HTTPStatus.CREATED

    assert caregiver_models.Device.objects.count() == 1
    assert caregiver_models.Device.objects.get().device_id == device_id


def test_device_put_update(api_client: APIClient, listener_user: User) -> None:
    """Test updating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)
    device = caregiver_factories.Device(caregiver=caregiver)
    last_modified = device.modified

    data = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }

    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data,
    )

    assert response.status_code == HTTPStatus.OK

    device.refresh_from_db()

    assert device.modified > last_modified


@pytest.mark.xfail(
    condition=True,
    reason='bug that prevents the same device to be used by multiple caregivers',
    strict=True,
)
def test_device_put_two_caregivers(api_client: APIClient, listener_user: User) -> None:
    """Test updating a device model."""
    api_client.force_login(listener_user)
    device_id = '3840166df22af52b5ac8fe757371c314d281ad3a83f1dd5f2e4df865'

    caregiver = caregiver_factories.CaregiverProfile()
    caregiver2 = caregiver_factories.CaregiverProfile()
    device = caregiver_factories.Device(caregiver=caregiver, device_id=device_id)
    device2 = caregiver_factories.Device(caregiver=caregiver2, device_id=device_id)

    last_modified = device.modified
    last_modified2 = device2.modified

    data = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }

    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data,
    )

    assert response.status_code == HTTPStatus.OK

    device.refresh_from_db()
    device2.refresh_from_db()

    assert device.modified > last_modified
    assert device2.modified == last_modified2


def test_create_device_failure(api_client: APIClient, listener_user: User) -> None:
    """Test failure for creating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)
    device = caregiver_factories.Device(caregiver=caregiver)

    data = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': 'bad_caregiver_pk',
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_device_success(api_client: APIClient, listener_user: User) -> None:
    """Test updating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)
    device = caregiver_factories.Device(  # noqa: S106
        caregiver=caregiver,
        type=caregiver_models.DeviceType.IOS,
        push_token='aaaa1111',
        is_trusted=False,
    )
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_one,
    )
    # Change device data for full update action
    data_two = {
        'device_id': device.device_id,
        'type': caregiver_models.DeviceType.ANDROID,
        'caregiver': caregiver.id,
        'is_trusted': True,
        'push_token': 'bbbb2222',
    }
    response_two = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_two,
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.OK


def test_update_device_failure(api_client: APIClient, listener_user: User) -> None:
    """Test failure for updating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)
    device = caregiver_factories.Device(  # noqa: S106
        caregiver=caregiver,
        type=caregiver_models.DeviceType.IOS,
        push_token='aaaa1111',
        is_trusted=False,
    )
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_one,
    )
    # Input invalid data
    data_two = {
        'device_id': device.device_id,
        'type': caregiver_models.DeviceType.ANDROID,
        'caregiver': caregiver.id,
        'is_trusted': 'fish',
        'push_token': 'bbbb2222',
    }
    response_two = api_client.put(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_two,
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.BAD_REQUEST


def test_partial_update_device_not_found(api_client: APIClient, listener_user: User) -> None:
    """Test partial updating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)

    device_id = '3840166df22af52b5ac8fe757371c314d281ad3a83f1dd5f2e4df865'

    data = {
        'device_id': device_id,
        'type': caregiver_models.DeviceType.IOS,
        'caregiver': caregiver.id,
        'is_trusted': False,
        'push_token': '2803df883164a7c8f12126f802a7d5fd08c361bca1e7b7a0acf88d361be54c4cc547b5a6c13141ecc5d7e',
    }

    response_one = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device_id},
        ),
        data=data,
    )
    assert response_one.status_code == HTTPStatus.NOT_FOUND


def test_partial_update_device_success(api_client: APIClient, listener_user: User) -> None:
    """Test partial updating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)
    device = caregiver_factories.Device(caregiver=caregiver)
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_one,
    )
    assert response_one.status_code == HTTPStatus.OK


def test_partial_update_device_failure(api_client: APIClient, listener_user: User) -> None:
    """Test failure for partial updating a device model."""
    api_client.force_login(listener_user)
    caregiver = caregiver_factories.CaregiverProfile(id=1)
    device = caregiver_factories.Device(  # noqa: S106
        caregiver=caregiver,
        type=caregiver_models.DeviceType.IOS,
        push_token='aaaa1111',
        is_trusted=False,
    )
    data_one = {
        'device_id': device.device_id,
        'type': device.type,
        'caregiver': caregiver.id,
        'is_trusted': device.is_trusted,
        'push_token': device.push_token,
    }
    response_one = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_one,
    )
    # Input invalid data
    data_two = {
        'device_id': device.device_id,
        'caregiver': caregiver.id,
        'is_trusted': 'fish',
    }
    response_two = api_client.patch(
        reverse(
            'api:devices-update-or-create',
            kwargs={'device_id': device.device_id},
        ),
        data=data_two,
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.BAD_REQUEST


class TestVerifyEmailCodeView:
    """A test class to test verifying an email with a code."""

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        registration_listener_user: User,
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:verify-email-code', kwargs={'code': '123456'})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(registration_listener_user)
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_verify_code_success(
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        """Test verify verification code success."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factories.CaregiverProfile()
        registration_code = caregiver_factories.RegistrationCode(relationship__caregiver=caregiver_profile)
        email_verification = caregiver_factories.EmailVerification(caregiver=caregiver_profile)
        user_email = caregiver_profile.user.email

        assert caregiver_models.EmailVerification.objects.count() == 1

        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': registration_code.code},
            ),
            data={
                'code': email_verification.code,
                'email': email_verification.email,
            },
        )

        caregiver_profile.user.refresh_from_db()
        email_verification.refresh_from_db()

        assert response.status_code == HTTPStatus.OK
        assert caregiver_profile.user.email == user_email
        assert caregiver_models.EmailVerification.objects.count() == 1
        assert email_verification.is_verified

    def test_verify_code_format_incorrect(self, api_client: APIClient, admin_user: User) -> None:
        """Test verification code format is incorrect."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()

        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': registration_code.code},
            ),
            data={'code': '1111', 'email': 'opal@muhc.mcgill.ca'},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data == {
            'code': [
                ErrorDetail(
                    string='Ensure this field has at least 6 characters.',
                    code='min_length',
                ),
            ],
        }

    def test_verify_code_invalid(self, api_client: APIClient, admin_user: User) -> None:
        """Test verification code invalid."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()

        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': registration_code.code},
            ),
            data={'code': '111666', 'email': 'opal@muhc.mcgill.ca'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='No EmailVerification matches the given query.',
                code='not_found',
            ),
        }

    def test_registration_code_invalid(self, api_client: APIClient, admin_user: User) -> None:
        """Test that an invalid registration code returns a not found error."""
        api_client.force_login(user=admin_user)

        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': '12345678'},
            ),
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='No RegistrationCode matches the given query.',
                code='not_found',
            ),
        }


class TestVerifyEmailView:
    """A test class to test the email verification API."""

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        registration_listener_user: User,
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:verify-email', kwargs={'code': '123456'})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(registration_listener_user)
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_save_verify_verification_created(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Test that the EmailVerification instance is created with the correct properties."""
        # mock the current timezone to simulate the UTC time already on the next day
        current_time = datetime(2022, 6, 2, 2, 0, tzinfo=dt.timezone.utc)
        mocker.patch.object(timezone, 'now', return_value=current_time)

        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()
        email = 'test@muhc.mcgill.ca'

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
        )

        assert response.status_code == HTTPStatus.OK

        email_verification = caregiver_models.EmailVerification.objects.get(email=email)

        assert not email_verification.is_verified
        assert email_verification.email == email
        assert email_verification.code
        assert email_verification.caregiver == registration_code.relationship.caregiver
        assert email_verification.sent_at == current_time

    def test_save_verify_email_sent(
        self,
        api_client: APIClient,
        admin_user: User,
        settings: SettingsWrapper,
    ) -> None:
        """Test that the email is sent when verifying an email address."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()
        email = 'test@muhc.mcgill.ca'

        api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
        )

        email_verification = caregiver_models.EmailVerification.objects.get(email=email)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].from_email == settings.EMAIL_FROM_REGISTRATION
        assert mail.outbox[0].to == [email]
        assert email_verification.code in mail.outbox[0].body
        assert 'Dear' in mail.outbox[0].body
        assert mail.outbox[0].subject == 'Opal Verification Code'

    def test_resend_verify_email_within_ten_sec(self, api_client: APIClient, admin_user: User) -> None:
        """Test resend verify email within 10 sec."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()
        email_verification = caregiver_factories.EmailVerification(
            caregiver=registration_code.relationship.caregiver,
            sent_at=timezone.now() - dt.timedelta(seconds=9),
        )

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email_verification.email},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data == [
            ErrorDetail(
                string='Please wait 10 seconds before requesting a new verification code.',
                code='invalid',
            ),
        ]

    def test_resend_verify_email_after_ten_sec(self, api_client: APIClient, admin_user: User) -> None:
        """Test resending the code after 10 sec."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()
        email_verification = caregiver_factories.EmailVerification(
            caregiver=registration_code.relationship.caregiver,
            sent_at=timezone.now() - dt.timedelta(seconds=10),
        )
        current_code = email_verification.code

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email_verification.email},
        )

        assert response.status_code == HTTPStatus.OK
        email_verification.refresh_from_db()
        assert email_verification.code != current_code

    def test_email_registered(
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        """Test that an existing email address is detected."""
        api_client.force_login(user=admin_user)
        email = 'test@muhc.mcgill.ca'
        caregiver = Caregiver.objects.create(email=email)
        relationship = patient_factories.Relationship(caregiver__user=caregiver)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data == [
            ErrorDetail(
                string='The email is already registered.',
                code='invalid',
            ),
        ]

    def test_registration_code_not_exists(self, api_client: APIClient, admin_user: User) -> None:
        """Test registration code not exists."""
        api_client.force_login(user=admin_user)
        caregiver_factories.RegistrationCode()

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': 'code12345677'},
            ),
            data={'email': 'test@muhc.mcgill.ca'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='No RegistrationCode matches the given query.',
                code='not_found',
            ),
        }

    def test_registration_code_registered(self, api_client: APIClient, admin_user: User) -> None:
        """Test registration code is already registered."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode(
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        )
        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': 'test@muhc.mcgill.ca'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='No RegistrationCode matches the given query.',
                code='not_found',
            ),
        }

    def test_input_email_format_incorrect(self, api_client: APIClient, admin_user: User) -> None:
        """Test input email format is incorrect."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode()

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': 'aaaaaaaa'},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data == {
            'email': [
                ErrorDetail(
                    string='Enter a valid email address.',
                    code='invalid',
                ),
            ],
        }

    def test_input_email_exists(self, api_client: APIClient, admin_user: User) -> None:
        """Test input email does exist already."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        email_verification = caregiver_factories.EmailVerification(caregiver=caregiver_profile)
        old_verification_code = email_verification.code

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email_verification.email},
        )

        email_verification.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert email_verification.code != old_verification_code


class TestEmailVerificationProcess:  # noqa: WPS338 (let the _prepare fixture be first)
    """Test the email verification process."""

    email = 'foo@bar.ca'
    code = 'abcdef123456'

    @pytest.fixture(autouse=True)
    def _prepare(self, api_client: APIClient, admin_user: User) -> None:
        """Prepare by requesting to verify an email address."""
        api_client.force_login(user=admin_user)
        skeleton = user_factories.Caregiver(
            first_name='Foo',
            last_name='Bar',
            is_active=False,
        )
        self.registration_code = caregiver_factories.RegistrationCode(
            relationship__caregiver__user=skeleton,
            code=self.code,
        )

        self._request_code(api_client)

    def _request_code(self, api_client: APIClient, email: str | None = None) -> None:
        """Request a verification code."""
        email = email or self.email
        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': self.code},
            ),
            data={'email': email},
        )

        assert response.status_code == HTTPStatus.OK

    def _verify_email(self, api_client: APIClient, email_verification: caregiver_models.EmailVerification) -> None:
        """Verify the email address with the code."""
        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': self.code},
            ),
            data={
                'code': email_verification.code,
                'email': email_verification.email,
            },
        )

        assert response.status_code == HTTPStatus.OK

    def test_email_verification_process(self, api_client: APIClient) -> None:
        """Test the email verification process."""
        email_verification = caregiver_models.EmailVerification.objects.get(email=self.email)
        self._verify_email(api_client, email_verification)

        email_verification.refresh_from_db()
        assert email_verification.is_verified

        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': self.code},
            ),
            data={
                'code': email_verification.code,
                'email': self.email,
            },
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_email_verification_process_resend(self, api_client: APIClient, mocker: MockerFixture) -> None:
        """Test the email verification process with resending a verification code."""
        email_verification = caregiver_models.EmailVerification.objects.get(email=self.email)

        self._verify_email(api_client, email_verification)

        # mock the current timezone to simulate a later time
        future = timezone.now() + dt.timedelta(minutes=10)
        mocker.patch.object(timezone, 'now', return_value=future)

        self._request_code(api_client)

        email_verification.refresh_from_db()
        assert email_verification.sent_at == future
        assert not email_verification.is_verified

    def test_verify_email_multiple(self, api_client: APIClient, admin_user: User) -> None:
        """Ensure that the registration process still works when a user verifies two different emails."""
        email_verification = caregiver_models.EmailVerification.objects.get(email=self.email)

        # verify the first email address
        self._verify_email(api_client, email_verification)

        # the user does a second email verification for a different email address
        self._request_code(api_client, email='bar@foo.ca')
        self._verify_email(api_client, caregiver_models.EmailVerification.objects.get(email='bar@foo.ca'))

        assert caregiver_models.EmailVerification.objects.filter(is_verified=True).count() == 2

        # the user finishes the registration
        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': self.code},
            ),
            data=TestRegistrationCompletionView.input_data,
        )

        user = self.registration_code.relationship.caregiver.user
        user.refresh_from_db()

        assert response.status_code == HTTPStatus.OK
        assert user.email == 'bar@foo.ca'


class TestRegistrationCompletionView:
    """Test class tests the api registration/<str: code>/register."""

    input_data = {
        'patient': {
            'legacy_id': 1,
        },
        'caregiver': {
            'language': 'fr',
            'phone_number': '+15141112222',
            'username': 'test-username',
            'legacy_id': 1,
        },
        'security_answers': [
            {
                'question': 'correct?',
                'answer': 'yes',
            },
            {
                'question': 'correct?',
                'answer': 'maybe',
            },
        ],
    }

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        registration_listener_user: User,
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:registration-register', kwargs={'code': '123456'})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(registration_listener_user)
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_register_success(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        skeleton = user_factories.Caregiver(
            username='skeleton-username',
            first_name='skeleton',
            last_name='test',
            is_active=False,
        )
        registration_code = caregiver_factories.RegistrationCode(relationship__caregiver__user=skeleton)
        caregiver_factories.EmailVerification(caregiver=registration_code.relationship.caregiver, is_verified=True)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
        )

        registration_code.refresh_from_db()
        security_answers = caregiver_models.SecurityAnswer.objects.all()
        assert response.status_code == HTTPStatus.OK
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED
        assert len(security_answers) == 2

    def test_existing_patient_caregiver(self, api_client: APIClient, admin_user: User) -> None:
        """Existing patient and caregiver don't cause the serializer to fail."""
        api_client.force_login(user=admin_user)
        Relationship(patient__legacy_id=1, caregiver__legacy_id=1)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': '123456'},
            ),
            data=self.input_data,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_non_existent_registration_code(self, api_client: APIClient, admin_user: User) -> None:
        """Test non-existent registration code."""
        api_client.force_login(user=admin_user)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': 'code11111111'},
            ),
            data=self.input_data,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_registered_registration_code(self, api_client: APIClient, admin_user: User) -> None:
        """Test registered registration code."""
        api_client.force_login(user=admin_user)
        registration_code = caregiver_factories.RegistrationCode(
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        )

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_register_with_invalid_input_data(self, api_client: APIClient, admin_user: User) -> None:
        """Test validation of patient's legacy_id."""
        api_client.force_login(user=admin_user)

        invalid_data: dict[str, Any] = copy.deepcopy(self.input_data)
        invalid_data['patient']['legacy_id'] = 0

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': '123456'},
            ),
            data=invalid_data,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {
            'patient': {'legacy_id': ['Ensure this value is greater than or equal to 1.']},
        }

    def test_register_with_invalid_phone(self, api_client: APIClient, admin_user: User) -> None:
        """Test validation of the phone number."""
        api_client.force_login(user=admin_user)

        skeleton = user_factories.Caregiver(
            username='skeleton-username',
            first_name='skeleton',
            last_name='test',
            is_active=False,
        )
        registration_code = caregiver_factories.RegistrationCode(relationship__caregiver__user=skeleton)
        caregiver_factories.EmailVerification(caregiver=registration_code.relationship.caregiver, is_verified=True)

        invalid_data: dict[str, Any] = copy.deepcopy(self.input_data)
        invalid_data['caregiver']['phone_number'] = '1234567890'

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=invalid_data,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {
            'detail': "({'phone_number': [ValidationError(['Enter a valid value.'])]}, None, None)",
        }
        # check that no data was changed
        registration_code.refresh_from_db()
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.NEW
        security_answers = caregiver_models.SecurityAnswer.objects.all()
        assert not security_answers

    def test_remove_skeleton_caregiver(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration register remove skeleton caregiver."""
        api_client.force_login(user=admin_user)
        # Build existing caregiver
        caregiver = user_factories.Caregiver(
            username='test-username',
            first_name='caregiver',
            last_name='test',
        )
        caregiver_profile = caregiver_factories.CaregiverProfile(user=caregiver)
        # Build skeleton user
        skeleton = user_factories.Caregiver(
            username='skeleton-username',
            first_name='skeleton',
            last_name='test',
        )
        skeleton_profile = caregiver_factories.CaregiverProfile(user=skeleton)
        # Build relationships: code -> relationship -> patient
        relationship = Relationship(caregiver=skeleton_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
        )

        registration_code.refresh_from_db()
        relationship.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED
        assert relationship.caregiver.id == caregiver_profile.id
        assert relationship.caregiver.user.id == caregiver.id
        assert not Caregiver.objects.filter(username=skeleton.username).exists()
        assert not caregiver_models.CaregiverProfile.objects.filter(user=skeleton).exists()

    def test_email_not_verified_new_caregiver(self, api_client: APIClient, admin_user: User) -> None:
        """The registration fails if the email address wasn't verified when it is a new caregiver."""
        api_client.force_login(user=admin_user)
        caregiver = caregiver_factories.CaregiverProfile(user__email='', user__is_active=False)
        registration_code = caregiver_factories.RegistrationCode(relationship__caregiver=caregiver)
        caregiver_factories.EmailVerification(
            caregiver=registration_code.relationship.caregiver,
            email='foo@bar.com',
            is_verified=False,
        )

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
        )

        assert response.status_code != HTTPStatus.OK
        registration_code.refresh_from_db()
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.NEW
        assert 'Caregiver email is not verified' in response.content.decode()

    def test_email_not_verified_existing_caregiver(self, api_client: APIClient, admin_user: User) -> None:
        """The registration succeeds with no email verification when it is an existing caregiver."""
        api_client.force_login(user=admin_user)
        # create an existing caregiver
        caregiver_factories.CaregiverProfile(user__username='test-username')
        caregiver = caregiver_factories.CaregiverProfile(
            user__first_name='Ske',
            user__last_name='leton',
            user__username='skeleton',
            user__email='',
        )
        registration_code = caregiver_factories.RegistrationCode(relationship__caregiver=caregiver)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
        )

        assert response.status_code == HTTPStatus.OK
        registration_code.refresh_from_db()
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED
        assert Caregiver.objects.count() == 1

    def test_verified_email_copied(self, api_client: APIClient, admin_user: User) -> None:
        """The verified email is copied to the caregiver."""
        api_client.force_login(user=admin_user)
        caregiver_user = user_factories.Caregiver(email='', is_active=False)
        registration_code = caregiver_factories.RegistrationCode(relationship__caregiver__user=caregiver_user)
        caregiver_factories.EmailVerification(
            caregiver=registration_code.relationship.caregiver,
            email='foo@bar.com',
            is_verified=True,
        )

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
        )

        assert response.status_code == HTTPStatus.OK

        registration_code.refresh_from_db()
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED
        caregiver_user.refresh_from_db()
        assert caregiver_user.email == 'foo@bar.com'
