# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for FHIR connector functionality."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2 import OAuth2Error
from pydantic import ValidationError
from pytest_mock import MockerFixture

from opal.services.fhir.fhir import FHIRConnector


class TestFHIRConnector:
    """Test cases for the FHIRConnector class."""

    @pytest.fixture
    def fhir_connector(self, mocker: MockerFixture) -> FHIRConnector:
        """A FHIRConnector instance with a mocked OAuth2 session."""
        mock_session = mocker.Mock(spec=OAuth2Session)
        mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

        return FHIRConnector(
            oauth_url='https://example.com/oauth',
            fhir_url='https://example.com/fhir',
            client_id='test_client',
            private_key='test_key',
        )

    def _mock_response(self, mocker: MockerFixture, data: dict[str, Any]) -> Mock:
        mock_response: Mock = mocker.Mock(spec=requests.Response)
        mock_response.status_code = requests.codes.ok
        mock_response.json.return_value = data

        return mock_response

    def _load_fixture(self, filename: str) -> dict[str, Any]:
        with Path(__file__).parent.joinpath('./fixtures').joinpath(filename).open(encoding='utf-8') as f:
            data: dict[str, Any] = json.load(f)
            return data

    def test_init(self, mocker: MockerFixture) -> None:
        """A token is fetched when initializing the FHIRConnector."""
        mock_session = mocker.Mock(spec=OAuth2Session)
        mock_oauth_class = mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

        connector = FHIRConnector(
            oauth_url='https://example.com/oauth',
            fhir_url='https://example.com/fhir',
            client_id='test_client',
            private_key='test_key',
        )

        assert connector.fhir_url == 'https://example.com/fhir'

        mock_oauth_class.assert_called_once()
        mock_session.fetch_token.assert_called_once_with('https://example.com/oauth/token')

    def test_init_invalid_private_key(self) -> None:
        """FHIRConnector initialization fails when an invalid private key is provided."""
        with pytest.raises(ValueError, match='Unable to load PEM file'):
            FHIRConnector(
                oauth_url='https://example.com/oauth',
                fhir_url='https://example.com/fhir',
                client_id='test_client',
                private_key='invalid_key',
            )

    def test_init_oauth_error(self, mocker: MockerFixture) -> None:
        """FHIRConnector initialization fails when OAuth2 authentication fails."""
        mock_session = mocker.Mock(spec=OAuth2Session)
        mock_session.fetch_token.side_effect = OAuth2Error('Client authentication failed')
        mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

        with pytest.raises(OAuth2Error, match='Client authentication failed'):
            FHIRConnector(
                oauth_url='https://example.com/oauth',
                fhir_url='https://example.com/fhir',
                client_id='invalid_client',
                private_key='test_key',
            )

        mock_session.fetch_token.assert_called_once_with('https://example.com/oauth/token')

    def test_init_connection_error(self, mocker: MockerFixture) -> None:
        """FHIRConnector initialization fails when network connection fails."""
        mock_session = mocker.Mock(spec=OAuth2Session)
        mock_session.fetch_token.side_effect = requests.ConnectionError('Connection failed')
        mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

        with pytest.raises(requests.ConnectionError, match='Connection failed'):
            FHIRConnector(
                oauth_url='https://example.com/oauth',
                fhir_url='https://example.com/fhir',
                client_id='test_client',
                private_key='test_key',
            )

        mock_session.fetch_token.assert_called_once_with('https://example.com/oauth/token')

    def test_init_http_error(self, mocker: MockerFixture) -> None:
        """FHIRConnector initialization fails when HTTP error occurs."""
        mock_session = mocker.Mock(spec=OAuth2Session)
        mock_session.fetch_token.side_effect = requests.HTTPError('500 Server Error')
        mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

        with pytest.raises(requests.HTTPError, match='500 Server Error'):
            FHIRConnector(
                oauth_url='https://example.com/oauth',
                fhir_url='https://example.com/fhir',
                client_id='test_client',
                private_key='test_key',
            )

        mock_session.fetch_token.assert_called_once_with('https://example.com/oauth/token')

    def test_find_patient(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Finding a patient by identifier returns the correct Patient resource."""
        patient_data = self._load_fixture('patient.json')
        mock_response = self._mock_response(mocker, patient_data)
        fhir_connector.session.get.return_value = mock_response

        patient = fhir_connector.find_patient('test-identifier')

        assert patient.id == '3a9a1eae-efb7-11ef-9c0b-fa163e7f8dbb'
        fhir_connector.session.get.assert_called_once_with(
            'https://example.com/fhir/Patient?identifier=test-identifier'
        )

    def test_find_patient_not_found(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Finding a patient by identifier raises a ValueError when no patient is found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValueError, match='No patient found with identifier test-identifier'):
            fhir_connector.find_patient('test-identifier')

    def test_find_patient_not_found_empty_entry(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Finding a patient by identifier raises a ValueError when no patient is found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0, 'entry': []}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValueError, match='No patient found with identifier test-identifier'):
            fhir_connector.find_patient('test-identifier')

    def test_find_patient_multiple_patients(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Finding a patient by identifier returns the correct Patient resource."""
        patient_data = self._load_fixture('patient.json')
        # Simulate multiple patients by duplicating the entry
        patient_data['entry'].append(patient_data['entry'][0])
        patient_data['total'] = 2
        mock_response = self._mock_response(mocker, patient_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValueError, match='Multiple patients found with identifier test-identifier'):
            fhir_connector.find_patient('test-identifier')

    def test_find_patient_invalid_data(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Finding a patient by identifier raises a ValidationError when the response data is invalid."""
        patient_data = self._load_fixture('patient.json')
        # Simulate invalid data to trigger a ValidationError (removing the whole key or other keys does not work since they are optional)
        patient_data['entry'][0]['resource']['name'][0]['family'] = ''
        mock_response = self._mock_response(mocker, patient_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValidationError, match=r'name.0.family\n\s+String should match pattern'):
            fhir_connector.find_patient('test-identifier')

    def test_patient_conditions(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient conditions returns the correct Condition resources."""
        conditions_data = self._load_fixture('conditions.json')
        mock_response = self._mock_response(mocker, conditions_data)
        fhir_connector.session.get.return_value = mock_response

        conditions = fhir_connector.patient_conditions('test-patient-uuid')

        assert len(conditions) == 2
        assert conditions[0].id == '9ef97f51-133a-4214-a1c5-e673c608073a'
        assert conditions[1].id == '9ef97ff8-b075-48a9-864b-a10a435ff81a'
        fhir_connector.session.get.assert_called_once_with(
            'https://example.com/fhir/Condition?patient=test-patient-uuid'
        )

    def test_patient_conditions_empty(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient conditions returns empty list when no conditions found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        conditions = fhir_connector.patient_conditions('test-patient-uuid')

        assert conditions == []

    def test_patient_conditions_data_sanitization(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Patient conditions data sanitization handles malformed code fields."""
        conditions_data = self._load_fixture('conditions.json')
        # Add trailing whitespace to code and empty display
        conditions_data['entry'][0]['resource']['code']['coding'][0]['code'] = 'B18.2   '
        conditions_data['entry'][1]['resource']['code']['coding'][0]['display'] = ''
        mock_response = self._mock_response(mocker, conditions_data)
        fhir_connector.session.get.return_value = mock_response

        conditions = fhir_connector.patient_conditions('test-patient-uuid')

        assert len(conditions) == 2
        # Verify sanitization worked
        assert conditions[0].code.coding[0].code == 'B18.2'
        assert conditions[1].code.coding[0].display == 'No display provided'

    def test_patient_conditions_invalid_data(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Patient conditions raises a ValidationError when FHIR data is invalid."""
        conditions_data = self._load_fixture('conditions.json')
        # Remove required subject field to trigger ValidationError
        conditions_data['entry'][0]['resource'].pop('subject')
        mock_response = self._mock_response(mocker, conditions_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValidationError, match=r'entry.0.resource.subject\n\s+Field required'):
            fhir_connector.patient_conditions('test-patient-uuid')

    def test_patient_medication_requests(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient medication requests returns the correct MedicationRequest resources."""
        medication_requests_data = self._load_fixture('medicationrequests.json')
        mock_response = self._mock_response(mocker, medication_requests_data)
        fhir_connector.session.get.return_value = mock_response

        medication_requests = fhir_connector.patient_medication_requests('test-patient-uuid')

        assert len(medication_requests) == 2
        assert medication_requests[0].id == '9efb5312-c612-4dbd-9f1b-381d531f83d7'
        assert medication_requests[1].id == '9ef98091-6d03-4e5c-ae98-f7826824db88'
        fhir_connector.session.get.assert_called_once_with(
            'https://example.com/fhir/MedicationRequest?patient=test-patient-uuid'
        )

    def test_patient_medication_requests_empty(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient medication requests returns an empty list when no medication requests found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        medication_requests = fhir_connector.patient_medication_requests('test-patient-uuid')

        assert medication_requests == []

    def test_patient_medication_requests_invalid_data(
        self, fhir_connector: FHIRConnector, mocker: MockerFixture
    ) -> None:
        """Patient medication requests raises a ValidationError when FHIR data is invalid."""
        medication_requests_data = self._load_fixture('medicationrequests.json')
        # Remove required subject field to trigger validation error
        medication_requests_data['entry'][0]['resource'].pop('subject')
        mock_response = self._mock_response(mocker, medication_requests_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValidationError, match=r'entry.0.resource.subject\n\s+Field required'):
            fhir_connector.patient_medication_requests('test-patient-uuid')

    def test_patient_allergies(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient allergies returns the correct AllergyIntolerance resources."""
        allergies_data = self._load_fixture('allergies.json')
        mock_response = self._mock_response(mocker, allergies_data)
        fhir_connector.session.get.return_value = mock_response

        allergies = fhir_connector.patient_allergies('test-patient-uuid')

        assert len(allergies) == 2
        assert allergies[0].id == '9ef97779-4410-4ffb-a8b8-36ef546b2021'
        assert allergies[1].id == 'a80b225b-1fa4-11f0-b78d-fa163e91b78d'
        fhir_connector.session.get.assert_called_once_with(
            'https://example.com/fhir/AllergyIntolerance?patient=test-patient-uuid'
        )

    def test_patient_allergies_empty(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient allergies returns an empty list when no allergies found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        allergies = fhir_connector.patient_allergies('test-patient-uuid')

        assert allergies == []

    def test_patient_allergies_invalid_data(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Patient allergies raises a ValidationError when FHIR data is invalid."""
        allergies_data = self._load_fixture('allergies.json')
        # Remove required patient field to trigger validation error
        allergies_data['entry'][0]['resource'].pop('patient')
        mock_response = self._mock_response(mocker, allergies_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValidationError, match=r'entry.0.resource.patient\n\s+Field required'):
            fhir_connector.patient_allergies('test-patient-uuid')

    def test_patient_immunizations(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient immunizations returns the correct Immunization resources."""
        immunizations_data = self._load_fixture('immunizations.json')
        mock_response = self._mock_response(mocker, immunizations_data)
        fhir_connector.session.get.return_value = mock_response

        immunizations = fhir_connector.patient_immunizations('test-patient-uuid')

        assert len(immunizations) == 2
        assert immunizations[0].id == '9efb5312-a894-4f8f-9bb3-f2640e405247'
        assert immunizations[1].id == '9efb5312-a8ed-4454-b6ee-b79b731ff31a'
        fhir_connector.session.get.assert_called_once_with(
            'https://example.com/fhir/Immunization?patient=test-patient-uuid'
        )

    def test_patient_immunizations_empty(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient immunizations returns an empty list when no immunizations found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        immunizations = fhir_connector.patient_immunizations('test-patient-uuid')

        assert immunizations == []

    def test_patient_immunizations_date_sanitization(
        self, fhir_connector: FHIRConnector, mocker: MockerFixture
    ) -> None:
        """Patient immunizations date sanitization handles invalid dates with -0001."""
        immunizations_data = self._load_fixture('immunizations.json')
        # Add invalid date with -0001 year
        immunizations_data['entry'][0]['resource']['meta']['lastUpdated'] = '-0001-11-30T00:00:00-04:00'
        mock_response = self._mock_response(mocker, immunizations_data)
        fhir_connector.session.get.return_value = mock_response

        immunizations = fhir_connector.patient_immunizations('test-patient-uuid')

        assert len(immunizations) == 2

        # Verify -0001 was replaced correctly
        expected_datetime = datetime.fromisoformat(f'{datetime.now(tz=UTC).year - 1}-11-30T00:00:00-04:00')

        assert expected_datetime == immunizations[0].meta.lastUpdated

    def test_patient_immunizations_invalid_data(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Patient immunizations raises ValidationError when FHIR data is invalid."""
        immunizations_data = self._load_fixture('immunizations.json')
        # Remove required patient field to trigger validation error
        immunizations_data['entry'][0]['resource'].pop('patient')
        mock_response = self._mock_response(mocker, immunizations_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValidationError, match=r'entry.0.resource.patient\n\s+Field required'):
            fhir_connector.patient_immunizations('test-patient-uuid')

    def test_patient_observations(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient observations returns the correct Observation resources."""
        observations_data = self._load_fixture('observations.json')
        mock_response = self._mock_response(mocker, observations_data)
        fhir_connector.session.get.return_value = mock_response

        observations = fhir_connector.patient_observations('test-patient-uuid')

        assert len(observations) == 6
        assert observations[0].id == '59ace158-3be6-11f0-9645-fa163e09c13a'
        assert observations[1].id == '59acedd7-3be6-11f0-9645-fa163e09c13a'
        fhir_connector.session.get.assert_called_once_with(
            'https://example.com/fhir/Observation?patient=test-patient-uuid'
        )

    def test_patient_observations_empty(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Retrieving patient observations returns an empty list when no observations found."""
        empty_data = {'resourceType': 'Bundle', 'type': 'collection', 'total': 0}
        mock_response = self._mock_response(mocker, empty_data)
        fhir_connector.session.get.return_value = mock_response

        observations = fhir_connector.patient_observations('test-patient-uuid')

        assert observations == []

    def test_patient_observations_invalid_data(self, fhir_connector: FHIRConnector, mocker: MockerFixture) -> None:
        """Patient observations raises a ValidationError when FHIR data is invalid."""
        observations_data = self._load_fixture('observations.json')
        # Remove required subject field to trigger validation error
        observations_data['entry'][0]['resource'].pop('subject')
        mock_response = self._mock_response(mocker, observations_data)
        fhir_connector.session.get.return_value = mock_response

        with pytest.raises(ValidationError, match=r'entry.0.resource.subject\n\s+Field required'):
            fhir_connector.patient_observations('test-patient-uuid')

    @pytest.mark.parametrize(
        'method_name',
        [
            'patient_conditions',
            'patient_medication_requests',
            'patient_allergies',
            'patient_immunizations',
            'patient_observations',
        ],
    )
    def test_patient_methods_connection_error(
        self,
        fhir_connector: FHIRConnector,
        method_name: str,
    ) -> None:
        """Patient methods raise a ConnectionError on connection errors."""
        fhir_connector.session.get.side_effect = requests.ConnectionError('Connection failed')

        method = getattr(fhir_connector, method_name)

        with pytest.raises(requests.ConnectionError, match='Connection failed'):
            method('test-patient-uuid')

    @pytest.mark.parametrize(
        'method_name',
        [
            'patient_conditions',
            'patient_medication_requests',
            'patient_allergies',
            'patient_immunizations',
            'patient_observations',
        ],
    )
    def test_patient_methods_http_error(
        self,
        fhir_connector: FHIRConnector,
        mocker: MockerFixture,
        method_name: str,
    ) -> None:
        """Patient methods raise an HTTPError on HTTP errors."""
        mock_response: Mock = mocker.Mock(spec=requests.Response)
        mock_response.raise_for_status.side_effect = requests.HTTPError('500 Server Error')
        fhir_connector.session.get.return_value = mock_response

        method = getattr(fhir_connector, method_name)

        with pytest.raises(requests.HTTPError, match='500 Server Error'):
            method('test-patient-uuid')
