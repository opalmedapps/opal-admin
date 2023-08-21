"""Test module for the REST API endpoints of the `test_results` app."""

import json
from typing import Any

from django.contrib.auth.models import Permission
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual
from rest_framework import status
from rest_framework.test import APIClient

from opal.hospital_settings.factories import Site
from opal.patients import models as patient_models
from opal.patients.factories import HospitalPatient, Patient, Relationship
from opal.users import factories as user_factories

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestCreatePathologyView:
    """Class wrapper for pathology reports endpoint tests."""

    def test_pathology_create_unauthorized(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        # Make a `POST` request without proper permissions.
        response = api_client.post(
            reverse('api:patient-pathology-create'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_pathology_create_success(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint can update patient info with no errors."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=self._get_valid_input_data()['patient'],
        )

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        HospitalPatient(
            patient=patient,
            mrn='9999996',
            site=Site(code='RVH'),
        )
        HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=Site(code='MGH'),
        )

        client = self._get_client_with_permissions(api_client)
        response = client.post(
            reverse('api:patient-pathology-create'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

    def _get_valid_input_data(self) -> dict[str, Any]:
        """Generate valid JSON data for creating pathology record.

        Returns:
            dict: valid JSON data
        """
        return {
            'patient': 'b63695a4-cb5d-4b5d-aa1f-351525458054',
            'observations': [{
                'identifier_code': 'test',
                'identifier_text': 'txt',
                'value': 'value',
                'observed_at': '1986-10-01 12:30:30',
            }],
            'notes': [{
                'note_source': 'test',
                'note_text': 'test',
            }],
            'type': 'L',
            'sending_facility': '',
            'receiving_facility': '',
            'collected_at': '1985-10-01 12:30:30',
            'received_at': '1986-10-01 10:30:30',
            'message_type': '',
            'message_event': '',
            'test_group_code': 'TEST',
            'test_group_code_description': 'TEST',
            'legacy_document_id': None,
            'reported_at': '1985-12-01 10:30:30',
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
            Permission.objects.get(codename='add_generaltest'),
            Permission.objects.get(codename='add_observation'),
            Permission.objects.get(codename='add_note'),
            Permission.objects.get(codename='change_patient'),
        )
        api_client.force_login(user=user)
        return api_client
