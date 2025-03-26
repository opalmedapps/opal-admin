"""Test module for registration api endpoints."""

from hashlib import sha512

from django.urls import reverse

from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factory
from opal.patients import factories as patient_factory
from opal.users.models import Caregiver, User


def test_get_caregiver_patient_list(api_client: APIClient, admin_user: User) -> None:
    """Test that the REST api endpoint to get the list of patient does not return a value if only self is found."""
    api_client.force_login(user=admin_user)
    relationship_type = patient_factory.RelationshipType(name='Mother')
    patient_factory.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert len(response.data) == 1
    assert response.status_code == 200


def test_get_caregiver_patient_list_no_patient(api_client: APIClient, admin_user: User) -> None:
    """Test that the REST api endpoint to get the list of patient does not return a value if only self is found."""
    api_client.force_login(user=admin_user)
    patient_factory.Relationship()
    caregiver = Caregiver.objects.get()
    api_client.credentials(HTTP_APPUSERID=caregiver.username)
    response = api_client.get(reverse('api:caregivers-patient-list'))
    assert response.status_code == 200
    assert not response.data


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
