"""Test module for the REST API endpoints of the `databank` app."""

import json
from typing import Any
from uuid import uuid4

from django.contrib.auth.models import Permission
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual
from rest_framework import status
from rest_framework.test import APIClient

from opal.patients.factories import Patient
from opal.users import factories as user_factories

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])

PATIENT_UUID = uuid4()


class TestCreateDatabankConsentView:
    """Class wrapper for databank endpoint tests."""

    def test_databank_consent_form_fixture(self, databank_consent_questionnaire_and_response: dict) -> None:
        """Test the fixture from conftest creates a proper consent questionnaire."""
        consenting_patient = databank_consent_questionnaire_and_response['patient']
        consent_questionnaire = databank_consent_questionnaire_and_response['questionnaire']
        assert consenting_patient
        assert consent_questionnaire
        assert consenting_patient.external_id == 51
        assert consent_questionnaire.title.content == 'Databank Consent Questionnaire'
        assert consent_questionnaire.purpose.title.content == 'Consent'

    def test_databank_consent_create_unauthorized(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        # Make a `POST` request without proper permissions.
        response = api_client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_databank_consent_create_patient_uuid_does_not_exist(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns an error if the patient with given UUID does not exist."""
        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()

        response = client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': PATIENT_UUID}),
            data=data,
            format='json',
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data={
                'detail': 'Not found.',
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_databank_consent_create_missing_data(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint doesn't accept partial data."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        client = self._get_client_with_permissions(api_client)
        response = client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': str(patient.uuid)}),
            data={
                'has_appointments': True,
                'has_diagnoses': True,
                'has_demographics': True,
                'has_labs': False,
                'has_questionnaires': False,
                'middle_name': 'Bert',
            },
            format='json',
        )

        assertContains(
            response=response,
            text='{"city_of_birth":["This field is required."]}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_databank_consent_create_blank_city_of_birth(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint doesn't accept a blank city of birth."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        client = self._get_client_with_permissions(api_client)
        response = client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': str(patient.uuid)}),
            data={
                'has_appointments': True,
                'has_diagnoses': True,
                'has_demographics': True,
                'has_labs': False,
                'has_questionnaires': False,
                'middle_name': 'Bert',
                'city_of_birth': '',
            },
            format='json',
        )

        assertContains(
            response=response,
            text='{"city_of_birth":["This field may not be blank."]}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_databank_consent_create_blank_middle_name(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint allows blank middle name (middle name not required for GUID)."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        client = self._get_client_with_permissions(api_client)
        response = client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': str(patient.uuid)}),
            data={
                'has_appointments': True,
                'has_diagnoses': True,
                'has_demographics': True,
                'has_labs': False,
                'has_questionnaires': False,
                'middle_name': '',
                'city_of_birth': 'ddd',
            },
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_databank_consent_create_success(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint can create databank consent for a full input with no errors."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        client = self._get_client_with_permissions(api_client)
        response = client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': str(patient.uuid)}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED

    def _get_valid_input_data(self) -> dict[str, Any]:
        """Generate valid JSON data for a DatabankConsent record.

        Returns:
            dict: valid JSON data
        """
        return {
            'has_appointments': True,
            'has_diagnoses': True,
            'has_demographics': True,
            'has_labs': False,
            'has_questionnaires': False,
            'middle_name': 'Juliet',
            'city_of_birth': 'Springfield',
        }

    def _get_client_with_permissions(self, api_client: APIClient) -> APIClient:
        """
        Add permissions to a user and authorize it.

        Returns:
            Authorized API client.
        """
        user = user_factories.User(
            username='nonhumanuser',
            first_name='nonhumanuser',
            last_name='nonhumanuser',
        )
        user.user_permissions.add(
            Permission.objects.get(codename='add_databankconsent'),
            Permission.objects.get(codename='change_patient'),
        )
        api_client.force_login(user=user)
        return api_client
