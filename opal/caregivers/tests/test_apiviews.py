"""Test module for registration api endpoints."""
from hashlib import sha512
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factory
from opal.caregivers import models as caregiver_model
from opal.patients import factories as patient_factory
from opal.users.models import Caregiver, User


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
    assert relationship_type.id == relationship.type_id
    assert relationship.patient_id == response.data[0]['patient_id']


def test_get_caregiver_patient_list_fields(api_client: APIClient, admin_user: User) -> None:
    """Test patient list endpoint to return a list of patients with the correct response fields."""
    api_client.force_login(user=admin_user)
    relationship_type = patient_factory.RelationshipType(name='Mother')
    patient_factory.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert response.data[0]['patient_id']
    assert response.data[0]['patient_legacy_id']
    assert response.data[0]['first_name']
    assert response.data[0]['last_name']
    assert response.data[0]['status']


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

    def test_save_verify_email_en_success(  # noqa: WPS218
        self,
        api_client: APIClient,
        admin_user: AbstractUser,
        settings: SettingsWrapper,
    ) -> None:
        """Test save verify email with English template success."""
        api_client.force_login(user=admin_user)
        caregiver_profile = caregiver_factory.CaregiverProfile()
        relationship = patient_factory.Relationship(caregiver=caregiver_profile)
        registration_code = caregiver_factory.RegistrationCode(relationship=relationship)
        email = 'test@muhc.mcgill.ca'
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        response = api_client.post(
            reverse(
                'api:verify-email',
                kwargs={'code': registration_code.code},
            ),
            data={'email': email},
            format='json',
            HTTP_ACCEPT_LANGUAGE='en',
        )
        email_verification = caregiver_model.EmailVerification.objects.get(email=email)
        assert response.status_code == HTTPStatus.OK
        assert email_verification
        assert not email_verification.is_verified
        assert len(mail.outbox) == 1
        assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
        assert email_verification.code in mail.outbox[0].body
        assert 'Dear' in mail.outbox[0].body
        assert mail.outbox[0].subject == 'Opal Verification Code'

    def test_save_verify_email_fr_success(  # noqa: WPS218
        self,
        api_client: APIClient,
        admin_user: AbstractUser,
        settings: SettingsWrapper,
    ) -> None:
        """Test save verify email withe French template success."""
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
            HTTP_ACCEPT_LANGUAGE='fr',
        )
        email_verification = caregiver_model.EmailVerification.objects.get(email=email)
        assert response.status_code == HTTPStatus.OK
        assert email_verification
        assert len(mail.outbox) == 1
        assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
        assert email_verification.code in mail.outbox[0].body

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
