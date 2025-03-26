"""Test module for the REST API endpoints of the `test_results` app."""
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from opal.hospital_settings.factories import Institution
from opal.legacy import models as legacy_models
from opal.legacy.factories import LegacyAliasExpressionFactory, LegacyPatientFactory, LegacySourceDatabaseFactory
from opal.patients import models as patient_models
from opal.patients.factories import Patient, Relationship
from opal.test_results import models as test_results_models
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

PATIENT_UUID = uuid4()


class TestCreatePathologyView:
    """Class wrapper for pathology reports endpoint tests."""

    def test_pathology_create_unauthenticated(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthenticated."""
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

    def test_pathology_create_unauthorized(
        self,
        user_api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        response = user_api_client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_pathology_create_patient_uuid_does_not_exist(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint returns an error if the patient with given UUID does not exist."""
        api_client.force_login(interface_engine_user)

        response = api_client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data={
                'detail': 'Not found.',
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pathology_create_raises_exception(
        self,
        api_client: APIClient,
        tmp_path: Path,
        mocker: MockerFixture,
        settings: SettingsWrapper,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint raises exception in case of unsuccessful insertion to the OpalDB.Documents table."""
        settings.PATHOLOGY_REPORTS_PATH = tmp_path
        Institution()

        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        LegacyPatientFactory(
            patientsernum=patient.legacy_id,
        )

        # mock the current timezone to simulate the local time
        generated_at = timezone.localtime(timezone.now())
        mocker.patch.object(timezone, 'now', return_value=generated_at)

        api_client.force_login(interface_engine_user)

        response = api_client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': patient.uuid}),
            data=self._get_valid_input_data(),
            format='json',
        )
        assertContains(
            response=response,
            text='An error occurred while inserting `LegacyDocument` record to the database.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        assert test_results_models.GeneralTest.objects.count() == 0
        assert legacy_models.LegacyDocument.objects.count() == 0

    def test_pathology_create_raises_site_not_exist_exception(
        self,
        api_client: APIClient,
        tmp_path: Path,
        mocker: MockerFixture,
        settings: SettingsWrapper,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint raises exception in case of not getting a Site instance via receiving facility."""
        settings.PATHOLOGY_REPORTS_PATH = tmp_path
        valid_data = self._get_valid_input_data()
        Institution()
        Site(code=valid_data.get('receiving_facility'))

        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        LegacyPatientFactory(
            patientsernum=patient.legacy_id,
        )

        # mock the current timezone to simulate the local time
        generated_at = timezone.localtime(timezone.now())
        mocker.patch.object(timezone, 'now', return_value=generated_at)

        api_client.force_login(interface_engine_user)

        valid_data.update({'receiving_facility': ''})
        response = api_client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': patient.uuid}),
            data=valid_data,
            format='json',
        )
        assertContains(
            response=response,
            text='Site matching query does not exist.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        assert test_results_models.GeneralTest.objects.count() == 0
        assert legacy_models.LegacyDocument.objects.count() == 0

    def test_pathology_create_success(
        self,
        api_client: APIClient,
        tmp_path: Path,
        mocker: MockerFixture,
        settings: SettingsWrapper,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can generate pathology report and save pathology records with no errors."""
        settings.PATHOLOGY_REPORTS_PATH = tmp_path
        Institution()

        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        LegacyPatientFactory(
            patientsernum=patient.legacy_id,
        )

        LegacySourceDatabaseFactory(
            source_database_name='Oacis',
        )

        LegacyAliasExpressionFactory(
            expression_name='Pathology',
            description='Pathology',
        )
        # mock the current timezone to simulate the local time
        generated_at = timezone.localtime(timezone.now())
        mocker.patch.object(timezone, 'now', return_value=generated_at)
        api_client.force_login(interface_engine_user)

        response = api_client.post(
            reverse('api:patient-pathology-create', kwargs={'uuid': patient.uuid}),
            data=self._get_valid_input_data(),
            format='json',
        )
        report_file_name = '{first_name}_{last_name}_{date}_pathology.pdf'.format(
            first_name=patient.first_name,
            last_name=patient.last_name,
            date=generated_at.strftime('%Y-%b-%d_%H-%M-%S'),
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert test_results_models.GeneralTest.objects.count() == 1
        assert legacy_models.LegacyDocument.objects.count() == 1
        assert legacy_models.LegacyDocument.objects.filter(originalfilename=report_file_name).count() == 1
        pathology_report = settings.PATHOLOGY_REPORTS_PATH / report_file_name
        assert pathology_report.is_file()

    def _get_valid_input_data(self) -> dict[str, Any]:
        """Generate valid JSON data for creating pathology record.

        Returns:
            dict: valid JSON data
        """
        return {
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
            'case_number': 'test-case-number',
        }
