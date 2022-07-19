"""Test module for registration api endpoints."""

from hashlib import sha512

from django.urls import reverse

from rest_framework.test import APIClient

from opal.caregivers.factories import RegistrationCode as codeFactory
from opal.patients.factories import HospitalPatient as hospitalPatientFactory
from opal.users.models import User


def test_regitration_encryption_return_values(api_client: APIClient, admin_user: User) -> None:
    """Test status code and registration code value."""
    api_client.force_login(user=admin_user)
    registration_code = codeFactory()
    hospitalPatientFactory(patient=registration_code.relationship.patient)
    request_hash = sha512(registration_code.code.encode()).hexdigest()
    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': request_hash}))
    assert response.status_code == 200
    assert response.data['code'] == registration_code.code


def test_regitration_encryption_with_invalid_hash(api_client: APIClient, admin_user: User) -> None:
    """Return 404 if the hash is invalid."""
    api_client.force_login(user=admin_user)
    registration_code = codeFactory()
    hospitalPatientFactory(patient=registration_code.relationship.patient)
    invalid_hash = sha512('badcode'.encode()).hexdigest()
    response = api_client.get(reverse('api:registration-by-hash', kwargs={'hash': invalid_hash}))
    assert response.status_code == 404
