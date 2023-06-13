"""Test module for registration api endpoints."""
import datetime as dt
from datetime import datetime
from hashlib import sha512
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factory
from opal.caregivers import models as caregiver_model
from opal.patients import factories as patient_factory
from opal.users.models import Caregiver, User


def test_get_caregiver_patient_list_missing_user_id_header(user_client: APIClient) -> None:
    """Test patient list endpoint to return a bad request if the `Appuserid` header is missing."""
    response = user_client.get(reverse('api:caregivers-patient-list'))
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_caregiver_patient_list_no_patient(api_client: APIClient, admin_user: User) -> None:
    """Test patient list endpoint to return an empty list if there is no relationship."""
    api_client.force_login(user=admin_user)
    caregiver = caregiver_factory.Caregiver()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert response.status_code == HTTPStatus.OK
    assert not response.data


def test_get_caregiver_patient_list_patient_id(api_client: APIClient, admin_user: User) -> None:
    """Test patient list endpoint to return a list of patients with the correct patient_id and relationship type."""
    api_client.force_login(user=admin_user)
    relationship_type = patient_factory.RelationshipType(name='Mother')
    relationship = patient_factory.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 1
    assert relationship.type_id == response.data[0]['relationship_type']['id']
    assert relationship.patient_id == response.data[0]['patient_id']


def test_get_caregiver_patient_list_fields(api_client: APIClient, admin_user: User) -> None:
    """Test patient list endpoint to return a list of patients with the correct response fields."""
    api_client.force_login(user=admin_user)
    relationship_type = patient_factory.RelationshipType(name='Mother')
    patient_factory.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))

    data_fields = [
        'patient_id',
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


def test_caregiver_profile(api_client: APIClient, admin_user: User) -> None:
    """The caregiver's profile is returned."""
    caregiver_profile = caregiver_factory.CaregiverProfile(user__username='johnwaynedabest')

    api_client.force_login(user=admin_user)
    api_client.credentials(HTTP_APPUSERID=caregiver_profile.user.username)
    response = api_client.get(reverse('api:caregivers-profile'))

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    expected_data = ['uuid', 'first_name', 'last_name', 'language', 'phone_number', 'username', 'devices']
    assert list(data.keys()) == expected_data
    assert data['username'] == 'johnwaynedabest'
    assert not data['devices']


def test_caregiver_profile_not_found(api_client: APIClient, admin_user: User) -> None:
    """A 404 is returned if the caregiver does not exist."""
    api_client.force_login(user=admin_user)
    api_client.credentials(HTTP_APPUSERID='johnwaynedabest')
    response = api_client.get(reverse('api:caregivers-profile'))

    assert response.status_code == HTTPStatus.NOT_FOUND
    # ensure that the response contains JSON
    response.json()


def test_caregiver_profile_missing_header(api_client: APIClient, admin_user: User) -> None:
    """An error is returned if the `Appuserid` header is missing."""
    api_client.force_login(user=admin_user)
    response = api_client.get(reverse('api:caregivers-profile'))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = response.json()

    assert 'detail' in data


def test_registration_encryption_return_values(api_client: APIClient, admin_user: User) -> None:
    """Test status code and registration code value."""
    api_client.force_login(user=admin_user)
    registration_code = caregiver_factory.RegistrationCode()
    patient_factory.HospitalPatient(patient=registration_code.relationship.patient)
    request_hash = sha512(registration_code.code.encode()).hexdigest()
    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': request_hash}))
    assert response.status_code == HTTPStatus.OK
    assert response.data['code'] == registration_code.code


def test_registration_encryption_invalid_hash(api_client: APIClient, admin_user: User) -> None:
    """Return 404 if the hash is invalid."""
    api_client.force_login(user=admin_user)
    registration_code = caregiver_factory.RegistrationCode()
    patient_factory.HospitalPatient(patient=registration_code.relationship.patient)
    invalid_hash = sha512('badcode'.encode()).hexdigest()
    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': invalid_hash}))
    assert response.status_code == HTTPStatus.NOT_FOUND


class TestApiEmailVerification:
    """A class to test model EmailVerification apis."""

    def test_verify_code_success(
        self,
        api_client: APIClient,
        admin_user: AbstractUser,
    ) -> None:
        """Test verify verification code success."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        user_email = caregiver_profile.user.email
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
        email_verification = caregiver_factory.EmailVerification(caregiver=caregiver_profile)
        assert caregiver_model.EmailVerification.objects.all().count() == 1
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
        assert caregiver_model.EmailVerification.objects.all().count() == 0

    def test_save_verify_verification_created(  # noqa: WPS218
        self,
        api_client: APIClient,
        admin_user: AbstractUser,
        mocker: MockerFixture,
    ) -> None:
        """Test that the EmailVerification instance is created with the correct properties."""
        # mock the current timezone to simulate the UTC time already on the next day
        current_time = datetime(2022, 6, 2, 2, 0, tzinfo=dt.timezone.utc)
        mocker.patch.object(timezone, 'now', return_value=current_time)

        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
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

        email_verification = caregiver_model.EmailVerification.objects.get(email=email)

        assert not email_verification.is_verified
        assert email_verification.email == email
        assert email_verification.code
        assert email_verification.caregiver == caregiver_profile
        assert email_verification.sent_at == current_time

    def test_save_verify_email_sent(  # noqa: WPS218
        self,
        api_client: APIClient,
        admin_user: AbstractUser,
        settings: SettingsWrapper,
    ) -> None:
        """Test that the email is sent when verifying an email address."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
        email = 'test@muhc.mcgill.ca'

        api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
        )

        email_verification = caregiver_model.EmailVerification.objects.get(email=email)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
        assert mail.outbox[0].to == [email]
        assert email_verification.code in mail.outbox[0].body
        assert 'Dear' in mail.outbox[0].body
        assert mail.outbox[0].subject == 'Opal Verification Code'

    def test_resend_verify_email_within_ten_sec(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test resend verify email within 10 sec."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
        email_verification = caregiver_factory.EmailVerification(
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

    def test_registration_code_not_exists(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test registration code not exists."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        caregiver_factory.RegistrationCode(relationship=relationship)
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

    def test_registration_code_registered(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test registration code is already registered."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(
            relationship=relationship,
            status=caregiver_model.RegistrationCodeStatus.REGISTERED,
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

    def test_verify_code_format_incorrect(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test verification code format is incorrect."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
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

    def test_verify_code_invalid(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test verification code invalid."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
        caregiver_factory.EmailVerification(caregiver=caregiver_profile)
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

    def test_input_email_format_incorrect(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test input email format is incorrect."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
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

    def test_input_email_exists(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test input email does exist already."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
        email_verification = caregiver_factory.EmailVerification(caregiver=caregiver_profile)
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
