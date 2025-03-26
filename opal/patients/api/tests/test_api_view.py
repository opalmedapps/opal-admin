"""Test module for the `patients` app REST API endpoints."""

from datetime import datetime
from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.hospital_settings.factories import Institution, Site
from opal.patients.factories import HospitalPatient, Patient, Relationship

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
