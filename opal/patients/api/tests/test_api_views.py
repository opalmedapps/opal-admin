"""Test module for the `patients` app REST API endpoints."""

import copy
from datetime import datetime
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone

import pytest
from rest_framework.test import APIClient

from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.caregivers.models import RegistrationCodeStatus, SecurityAnswer
from opal.hospital_settings.factories import Institution, Site
from opal.patients.factories import HospitalPatient, Patient, Relationship
from opal.users.factories import User

pytestmark = pytest.mark.django_db


def test_my_caregiver_list(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test the return of the caregivers list for a given patient."""
    api_client.force_login(user=admin_user)
    patient = Patient()
    caregiver1 = CaregiverProfile()
    caregiver2 = CaregiverProfile()
    relationship1 = Relationship(patient=patient, caregiver=caregiver1)
    relationship2 = Relationship(patient=patient, caregiver=caregiver2, status='CON')
    api_client.credentials(HTTP_APPUSERID=caregiver2.user.username)
    response = api_client.get(reverse(
        'api:caregivers-list',
        kwargs={'legacy_id': patient.legacy_id},
    ))
    assert response.status_code == HTTPStatus.OK
    assert response.json()[0] == {
        'caregiver_id': caregiver1.user.id,
        'first_name': caregiver1.user.first_name,
        'last_name': caregiver1.user.last_name,
        'status': relationship1.status,
    }
    assert response.json()[1] == {
        'caregiver_id': caregiver2.user.id,
        'first_name': caregiver2.user.first_name,
        'last_name': caregiver2.user.last_name,
        'status': relationship2.status,
    }


def test_my_caregiver_list_failure(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test the failure of the caregivers list for a given patient."""
    api_client.force_login(user=admin_user)
    patient = Patient()
    caregiver1 = CaregiverProfile()
    caregiver2 = CaregiverProfile()
    Relationship(patient=patient, caregiver=caregiver1)
    Relationship(patient=patient, caregiver=caregiver2)
    api_client.credentials(HTTP_APPUSERID=caregiver1.user.username)

    response = api_client.get(reverse(
        'api:caregivers-list',
        kwargs={'legacy_id': 1654161},
    ))
    assert response.data['detail'] == 'Caregiver does not have a relationship with the patient.'
    assert response.status_code == HTTPStatus.FORBIDDEN


class TestApiRetrieveRegistrationDetails:
    """A class to test RetrieveRegistrationDetails apis."""

    def test_api_retrieve_registration(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration code with summary serializer."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        relationship = Relationship(patient=patient)
        registration_code = RegistrationCode(relationship=relationship)

        # Build relationships: hospital_patient -> site -> institution
        institution = Institution()
        site = Site(institution=institution)
        hospital_patient = HospitalPatient(patient=patient, site=site)

        response = api_client.get(reverse(
            'api:registration-code',
            kwargs={'code': registration_code.code},
        ))
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'patient': {
                'first_name': hospital_patient.patient.first_name,
                'last_name': hospital_patient.patient.last_name,
            },
            'institution': {
                'id': institution.id,
                'name': institution.name,
            },
        }

    def test_api_not_retrieve_deceased_patient(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration code with summary serializer not retrieve deceased patient."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        date_of_death = timezone.make_aware(datetime(2099, 9, 27))
        patient = Patient(date_of_death=date_of_death)
        relationship = Relationship(patient=patient)
        registration_code = RegistrationCode(relationship=relationship)

        response = api_client.get(reverse(
            'api:registration-code',
            kwargs={'code': registration_code.code},
        ))
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json() == {'detail': 'You do not have permission to perform this action.'}

    def test_registration_code_detailed(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration code with detailed serializer."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        relationship = Relationship(patient=patient)
        registration_code = RegistrationCode(relationship=relationship)

        # Build relationships: hospital_patient -> site -> institution
        institution = Institution()
        site = Site(institution=institution)
        hospital_patient = HospitalPatient(patient=patient, site=site)

        response = api_client.get(
            '{0}{1}'.format(
                reverse(
                    'api:registration-code',
                    kwargs={'code': registration_code.code},
                ),
                '?detailed',
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'patient': {
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'date_of_birth': datetime.strftime(patient.date_of_birth, '%Y-%m-%d'),
                'sex': patient.sex,
                'ramq': patient.ramq,
            },
            'hospital_patients': [
                {
                    'mrn': hospital_patient.mrn,
                    'site_code': site.code,
                },
            ],
        }


class TestApiRegistrationCompletion:
    """Test class tests the api registration/<str: code>/register."""

    valid_input_data = dict({
        'patient': {
            'legacy_id': 1,
        },
        'caregiver': {
            'language': 'fr',
            'phone_number': '+15141112222',
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
    })

    def test_register_success(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        valid_input_data = copy.deepcopy(self.valid_input_data)
        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=valid_input_data,
            format='json',
        )
        registration_code.refresh_from_db()
        security_answers = SecurityAnswer.objects.all()
        assert response.status_code == HTTPStatus.OK
        assert registration_code.status == RegistrationCodeStatus.REGISTERED
        assert len(security_answers) == 2

    def test_non_existent_registration_code(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test non-existent registration code."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        RegistrationCode(relationship=relationship)
        valid_input_data = copy.deepcopy(self.valid_input_data)
        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': 'code11111111'},
            ),
            data=valid_input_data,
            format='json',
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_registered_registration_code(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test registered registration code."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(
            relationship=relationship,
            status=RegistrationCodeStatus.REGISTERED,
        )
        valid_input_data = copy.deepcopy(self.valid_input_data)
        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=valid_input_data,
            format='json',
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_register_with_invalid_input_data(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        invalid_data: dict = copy.deepcopy(self.valid_input_data)
        invalid_data['patient']['legacy_id'] = 0

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=invalid_data,
            format='json',
        )

        registration_code.refresh_from_db()
        security_answers = SecurityAnswer.objects.all()
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert registration_code.status == RegistrationCodeStatus.NEW
        assert not security_answers
        assert response.json() == {
            'patient': {'legacy_id': ['Ensure this value is greater than or equal to 1.']},
        }

    def test_register_with_invalid_phone(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        invalid_data: dict = copy.deepcopy(self.valid_input_data)
        invalid_data['caregiver']['phone_number'] = '1234567890'

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=invalid_data,
            format='json',
        )

        registration_code.refresh_from_db()
        security_answers = SecurityAnswer.objects.all()
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert registration_code.status == RegistrationCodeStatus.NEW
        assert not security_answers
        assert response.json() == {
            'detail': "({'phone_number': [ValidationError(['Enter a valid value.'])]}, None, None)",
        }
