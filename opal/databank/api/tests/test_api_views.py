"""Test module for the REST API endpoints of the `databank` app."""
import json
from typing import Any, Callable
from uuid import uuid4

from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual
from rest_framework import status
from rest_framework.test import APIClient

from opal.patients.factories import Patient
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

PATIENT_UUID = uuid4()


class TestCreateDatabankConsentView:
    """Class wrapper for databank endpoint tests."""

    def test_databank_consent_create_unauthenticated(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthenticated."""
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

    def test_databank_consent_create_unauthorized(
        self,
        user_api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        response = user_api_client.post(
            reverse('api:databank-consent-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_databank_consent_create_patient_uuid_does_not_exist(
        self,
        api_client: APIClient,
        user_with_permission: Callable[[str | list[str]], User],
    ) -> None:
        """Ensure the endpoint returns an error if the patient with given UUID does not exist."""
        api_client.force_login(user_with_permission('databank.add_databankconsent'))
        data = self._get_valid_input_data()

        response = api_client.post(
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
        user_with_permission: Callable[[str | list[str]], User],
    ) -> None:
        """Ensure the endpoint can create databank consent with no errors."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        api_client.force_login(user_with_permission('databank.add_databankconsent'))

        response = api_client.post(
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
