"""Test module for the `patients` app REST API endpoints."""

from datetime import datetime
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.caregivers.models import RegistrationCodeStatus, SecurityAnswer
from opal.hospital_settings.factories import Institution, Site
from opal.users.factories import User

from ..factories import HospitalPatient, Patient, Relationship

pytestmark = pytest.mark.django_db


def test_registration_code(api_client: APIClient, admin_user: AbstractUser) -> None:
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


def test_registration_code_detailed(api_client: APIClient, admin_user: AbstractUser) -> None:
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
    print(response.json())
    print(
        {
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
    )
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


class TestApiRegistrationRegister:
    """Test class tests the api registration/<str: code>/register."""

    def test_register_success(sefl, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        valid_input_data = {
            'patient': {
                'legacy_id': 1,
            },
            'caregiver': {
                'language': 'fr',
                'phone_number': '+15141112222',
                'email': 'aaa@aaa.com',
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
            },
        }

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
        assert response.json() == {
            'detail': 'Saved the patient data successfully.',
        }

    def test_register_with_invalid_input_data(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        valid_input_data = {
            'patient': {
                'legacy_id': 0,
            },
            'caregiver': {
                'language': 'fr',
                'phone_number': '+15141112222',
                'email': 'aaaaaaaaa',
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
            },
        }

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
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert registration_code.status == RegistrationCodeStatus.NEW
        assert not security_answers
        assert response.json() == {
            'patient': {'legacy_id': ['Ensure this value is greater than or equal to 1.']},
        }

    def test_register_with_invalid_email(self, api_client: APIClient, admin_user: AbstractUser) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        user = User()
        caregiver = CaregiverProfile(user=user)
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        valid_input_data = {
            'patient': {
                'legacy_id': 1,
            },
            'caregiver': {
                'language': 'fr',
                'phone_number': '+15141112222',
                'email': 'aaaaaaaaa',
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
            },
        }

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
        assert registration_code.status == RegistrationCodeStatus.NEW
        assert not security_answers
        assert response.json() == {
            'detail': "({'email': [ValidationError(['Enter a valid email address.'])]}, None, None)",
        }
