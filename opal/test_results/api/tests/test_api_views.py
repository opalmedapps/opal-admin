"""Test module for the REST API endpoints of the `test_results` app."""

import json
from typing import Any
from uuid import uuid4

from django.contrib.auth.models import Permission
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from opal.patients import models as patient_models
from opal.patients.factories import HospitalPatient, Patient, Relationship
from opal.test_results.api.serializers import PatientUUIDRelatedField
from opal.users import factories as user_factories

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

PATIENT_UUID = uuid4()


class TestCreatePathologyView:
    """Class wrapper for pathology reports endpoint tests."""

    def test_pathology_create_unauthorized(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        # Make a `POST` request without proper permissions.
        response = api_client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_pathology_create_with_empty_uuid(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns an error if the patient's UUID field is empty."""
        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()
        data['patient'] = ''

        response = client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': PATIENT_UUID}),
            data=data,
            format='json',
        )

        assertContains(
            response=response,
            text='This field may not be null.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_pathology_create_empty_patient_queryset(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns an error if the patient queryset is empty."""
        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()
        data['patient'] = PATIENT_UUID

        response = client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': PATIENT_UUID}),
            data=data,
            format='json',
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data={
                'patient': ['Empty queryset. Expected a `QuerySet[Patient]`.'],
            },
        )

    def test_pathology_create_patient_uuid_does_not_exist(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns an error if the patient with given UUID does not exist."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=self._get_valid_input_data()['patient'],
        )

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()
        data['patient'] = PATIENT_UUID

        response = client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': PATIENT_UUID}),
            data=data,
            format='json',
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data={
                'patient': [f'Invalid UUID \"{PATIENT_UUID}\" - patient does not exist.'],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pathology_create_incorrect_queryset_type(
        self,
        api_client: APIClient,
        mocker: MockerFixture,
    ) -> None:
        """Ensure the endpoint returns an error if the `PatientUUIDRelatedField` uses incorrect queryset type."""
        HospitalPatient()
        mocker.patch.dict(
            'opal.test_results.api.serializers.PathologySerializer._declared_fields',
            {'patient': PatientUUIDRelatedField(queryset=patient_models.HospitalPatient.objects.all())},
        )

        patient = Patient(
            ramq='TEST01161972',
            uuid=self._get_valid_input_data()['patient'],
        )

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()

        response = client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': patient.uuid}),
            data=data,
            format='json',
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data={
                'patient': [
                    '{0} {1} {2}'.format(
                        'Incorrect queryset type.',
                        'Expected a `QuerySet[Patient]`,',
                        "but got <class 'opal.patients.models.HospitalPatient'>",
                    ),
                ],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

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

        client = self._get_client_with_permissions(api_client)
        response = client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': patient.uuid}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED

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
