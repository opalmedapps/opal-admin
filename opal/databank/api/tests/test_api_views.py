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

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

PATIENT_UUID = uuid4()


class TestCreateDatabankConsentView:
    """Class wrapper for databank endpoint tests."""

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

    def test_databank_consent_create_success(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint can create databank consent with no errors."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        patient.save()

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
