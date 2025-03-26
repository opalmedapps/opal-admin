"""Test module for registration api endpoints."""

from hashlib import sha512

from django.urls import reverse

from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factory
from opal.patients import factories as patient_factory
from opal.users.models import Caregiver, User


def test_get_caregiver_patient_list_no_patient(api_client: APIClient, admin_user: User) -> None:
    """Test patient list endpoint to return an empty list if their is not relationship."""
    api_client.force_login(user=admin_user)
    caregiver = caregiver_factory.Caregiver()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert response.status_code == 200
    assert not response.data


def test_get_caregiver_patient_list_patient_id(api_client: APIClient, admin_user: User) -> None:
    """Test patient list endpoint to return a list of patients with the correct patient_id and relationship type."""
    api_client.force_login(user=admin_user)
    relationship_type = patient_factory.RelationshipType(name='Mother')
    relationship = patient_factory.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert response.status_code == 200
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


def test_regitration_encryption_return_values(api_client: APIClient, admin_user: User) -> None:
    """Test status code and registration code value."""
    api_client.force_login(user=admin_user)
    registration_code = caregiver_factory.RegistrationCode()
    patient_factory.HospitalPatient(patient=registration_code.relationship.patient)
    request_hash = sha512(registration_code.code.encode()).hexdigest()
    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': request_hash}))
    assert response.status_code == 200
    assert response.data['code'] == registration_code.code


def test_regitration_encryption_with_invalid_hash(api_client: APIClient, admin_user: User) -> None:
    """Return 404 if the hash is invalid."""
    api_client.force_login(user=admin_user)
    registration_code = caregiver_factory.RegistrationCode()
    patient_factory.HospitalPatient(patient=registration_code.relationship.patient)
    invalid_hash = sha512('badcode'.encode()).hexdigest()
    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': invalid_hash}))
    assert response.status_code == 404
