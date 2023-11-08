"""Test module for registration api endpoints."""
import datetime as dt
from datetime import datetime
from hashlib import sha512
from http import HTTPStatus

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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
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
        format='json',
    )
    assert response_one.status_code == HTTPStatus.OK
    assert response_two.status_code == HTTPStatus.BAD_REQUEST


class TestVerifyEmailCodeView:
    """A test class to test the email code verification API."""

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
        user_email = caregiver_profile.user.email
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        email_verification = caregiver_factories.EmailVerification(caregiver=caregiver_profile)
        assert caregiver_models.EmailVerification.objects.all().count() == 1

        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': registration_code.code},
            ),
            data={
                'code': email_verification.code,
                'email': email_verification.email,
            },
            format='json',
        )

        caregiver_profile.user.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert caregiver_profile.user.email != user_email
        assert caregiver_profile.user.email == 'opal@muhc.mcgill.ca'
        assert caregiver_models.EmailVerification.objects.all().count() == 0

    def test_verify_code_format_incorrect(self, api_client: APIClient, admin_user: User) -> None:
        """Test verification code format is incorrect."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': registration_code.code},
            ),
            data={'code': '1111', 'email': 'opal@muhc.mcgill.ca'},
            format='json',
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
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        caregiver_factories.EmailVerification(caregiver=caregiver_profile)
        response = api_client.post(
            reverse(
                'api:verify-email-code',
                kwargs={'code': registration_code.code},
            ),
            data={'code': '111666', 'email': 'opal@muhc.mcgill.ca'},
            format='json',
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='Not found.',
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

    def test_save_verify_verification_created(  # noqa: WPS218
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
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        email = 'test@muhc.mcgill.ca'

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
        )

        assert response.status_code == HTTPStatus.OK

        email_verification = caregiver_models.EmailVerification.objects.get(email=email)

        assert not email_verification.is_verified
        assert email_verification.email == email
        assert email_verification.code
        assert email_verification.caregiver == caregiver_profile
        assert email_verification.sent_at == current_time

    def test_save_verify_email_sent(  # noqa: WPS218
        self,
        api_client: APIClient,
        admin_user: User,
        settings: SettingsWrapper,
    ) -> None:
        """Test that the email is sent when verifying an email address."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        email = 'test@muhc.mcgill.ca'

        api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
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
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        email_verification = caregiver_factories.EmailVerification(
            caregiver=caregiver_profile,
            sent_at=timezone.now(),
        )

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email_verification.email},
            format='json',
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data == [
            ErrorDetail(
                string='Please wait 10 seconds before requesting a new verification code.',
                code='invalid',
            ),
        ]

    def test_registered_confirmation_email_sent(  # noqa: WPS218
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        """Test that the registered confirmation email is sent when verifying an email address."""
        api_client.force_login(user=admin_user)
        email = 'test@muhc.mcgill.ca'
        caregiver = Caregiver(email=email)
        caregiver.save()
        caregiver_profile = caregiver_factories.CaregiverProfile(user=caregiver)
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)

        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
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
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        caregiver_factories.RegistrationCode(relationship=relationship)
        email = 'test@muhc.mcgill.ca'
        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': 'code12345677'},
            ),
            data={'email': email},
            format='json',
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='Not found.',
                code='not_found',
            ),
        }

    def test_registration_code_registered(self, api_client: APIClient, admin_user: User) -> None:
        """Test registration code is already registered."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(
            relationship=relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        )
        email = 'test@muhc.mcgill.ca'
        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.data == {
            'detail': ErrorDetail(
                string='Not found.',
                code='not_found',
            ),
        }

    def test_input_email_format_incorrect(self, api_client: APIClient, admin_user: User) -> None:
        """Test input email format is incorrect."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factories.CaregiverProfile()
        relationship = patient_factories.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factories.RegistrationCode(relationship=relationship)
        email = 'aaaaaaaa'
        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
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
            format='json',
        )
        email_verification.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert email_verification.code != old_verification_code
