# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2 import OAuth2Error
from fhir.resources.R4B.bundle import Bundle
from joserfc import jwe, jwk, util

from opal.services.fhir.fhir import FHIRConnector
from opal.services.fhir.utils import (
    FHIRConnectionSettings,
    FHIRDataRetrievalError,
    jwe_sh_link_encrypt,
    retrieve_patient_summary,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture

FHIR_SETTINGS = FHIRConnectionSettings(
    oauth_url='https://example.com/oauth2',
    fhir_url='https://example.com/fhir',
    client_id='test-client-id',
    private_key='private-key',
)


def test_jwe_sh_link_encrypt() -> None:
    """The encrypted data can be decrypted correctly."""
    data = 'secret data'
    raw_key, encrypted = jwe_sh_link_encrypt(data)

    # Key should be exactly 43 characters (32 bytes of randomness -> base64 encoded without padding)
    assert len(raw_key) == 43, f'Key length is {len(raw_key)}, expected 43 characters'

    key_decoded = util.urlsafe_b64decode(raw_key.encode('utf-8'))
    key = jwk.OctKey.import_key(key_decoded)

    decrypted = jwe.decrypt_compact(encrypted, key).plaintext

    assert decrypted is not None
    assert decrypted.decode('utf-8') == data


def test_jwe_sh_link_encrypt_empty() -> None:
    """Empty encrypted data can be encrypted and decrypted correctly."""
    data = ''
    raw_key, encrypted = jwe_sh_link_encrypt(data)

    key_decoded = util.urlsafe_b64decode(raw_key.encode('utf-8'))
    key = jwk.OctKey.import_key(key_decoded)

    decrypted = jwe.decrypt_compact(encrypted, key).plaintext

    assert decrypted is not None
    assert decrypted.decode('utf-8') == data


def test_jwe_sh_link_encrypt_different() -> None:
    """Encrypting the same data twice should yield different results."""
    data = '{"foo": "bar"}'

    key1, encrypted1 = jwe_sh_link_encrypt(data)
    key2, encrypted2 = jwe_sh_link_encrypt(data)

    assert key1 != key2, 'Keys should be different'
    assert encrypted1 != encrypted2, 'Encrypted data should be different'


def test_jwe_sh_link_encrypt_smart_health_links_compliance() -> None:
    """Test compliance with SMART Health Links specification requirements."""
    data = '{"resourceType": "Patient", "id": "example"}'
    _key, encrypted = jwe_sh_link_encrypt(data)

    # Parse the JWE compact serialization (header.encrypted_key.iv.ciphertext.tag)
    jwe_parts = encrypted.decode('utf-8').split('.')

    assert len(jwe_parts) == 5, 'JWE should have 5 parts in compact serialization'

    # Decode and verify the JWE header
    header_json = base64.urlsafe_b64decode(jwe_parts[0] + '==').decode('utf-8')
    header = json.loads(header_json)

    # Verify SMART Health Links specification compliance
    # https://build.fhir.org/ig/HL7/smart-health-cards-and-links/links-specification.html#encrypting-and-decrypting-files
    assert header['alg'] == 'dir', 'Algorithm should be "dir" (direct encryption)'
    assert header['enc'] == 'A256GCM', 'Encryption should be "A256GCM" (AES-256 GCM)'
    assert header['cty'] == 'application/fhir+json', 'Content type should be "application/fhir+json"'

    # Verify encrypted_key is empty (as required for "dir" algorithm)
    assert jwe_parts[1] == '', 'Encrypted key should be empty for direct encryption'


def test_retrieve_patient_summary(mocker: MockerFixture) -> None:
    """The patient data is fetched and the patient summary built correctly."""
    with Path(__file__).parent.joinpath('fixtures').joinpath('patient.json').open(encoding='utf-8') as f:
        patient = Bundle.model_validate_json(f.read()).entry[0].resource

    mock_fhir_connector = mocker.Mock(spec=FHIRConnector)
    mock_fhir_connector.find_patient.return_value = patient
    mock_fhir_connector.patient_conditions.return_value = []
    mock_fhir_connector.patient_medication_requests.return_value = []
    mock_fhir_connector.patient_allergies.return_value = []
    mock_fhir_connector.patient_observations.return_value = []
    mock_fhir_connector.patient_immunizations.return_value = []
    mocker.patch('opal.services.fhir.utils.FHIRConnector', return_value=mock_fhir_connector)

    summary_json, summary_uuid = retrieve_patient_summary(
        settings=FHIR_SETTINGS,
        identifier='test-identifier',
    )

    summary = Bundle.model_validate_json(summary_json)
    assert summary.identifier.value == summary_uuid


def test_retrieve_patient_summary_social_history_validated(mocker: MockerFixture) -> None:
    """The social history observations are validated."""
    with Path(__file__).parent.joinpath('fixtures').joinpath('patient.json').open(encoding='utf-8') as f:
        patient = Bundle.model_validate_json(f.read()).entry[0].resource

    with Path(__file__).parent.joinpath('fixtures', 'social_history.json').open() as f:
        social_history = json.load(f)

    social_history[0]['subject'] = {'type': 'Patient'}
    social_history[1]['subject'] = {'type': 'Patient'}

    mock_fhir_connector = mocker.Mock(spec=FHIRConnector)
    mock_fhir_connector.find_patient.return_value = patient
    mock_fhir_connector.patient_conditions.return_value = []
    mock_fhir_connector.patient_medication_requests.return_value = []
    mock_fhir_connector.patient_allergies.return_value = []
    mock_fhir_connector.patient_observations.return_value = []
    mock_fhir_connector.patient_immunizations.return_value = []
    mocker.patch('opal.services.fhir.utils.FHIRConnector', return_value=mock_fhir_connector)

    with pytest.raises(FHIRDataRetrievalError, match='Error validating social history observations'):
        retrieve_patient_summary(settings=FHIR_SETTINGS, identifier='test-identifier', social_history=social_history)


def test_retrieve_patient_summary_social_history_id_generated(mocker: MockerFixture) -> None:
    """The social history observations get an ID if missing."""
    with Path(__file__).parent.joinpath('fixtures').joinpath('patient.json').open(encoding='utf-8') as f:
        patient = Bundle.model_validate_json(f.read()).entry[0].resource

    with Path(__file__).parent.joinpath('fixtures', 'social_history.json').open() as f:
        social_history = json.load(f)

    social_history[0]['id'] = None
    social_history[1]['id'] = None

    mock_fhir_connector = mocker.Mock(spec=FHIRConnector)
    mock_fhir_connector.find_patient.return_value = patient
    mock_fhir_connector.patient_conditions.return_value = []
    mock_fhir_connector.patient_medication_requests.return_value = []
    mock_fhir_connector.patient_allergies.return_value = []
    mock_fhir_connector.patient_observations.return_value = []
    mock_fhir_connector.patient_immunizations.return_value = []
    mocker.patch('opal.services.fhir.utils.FHIRConnector', return_value=mock_fhir_connector)

    summary_json, summary_uuid = retrieve_patient_summary(
        settings=FHIR_SETTINGS,
        identifier='test-identifier',
        social_history=social_history,
    )

    summary = Bundle.model_validate_json(summary_json)
    assert summary.identifier.value == summary_uuid

    social_history_1 = summary.entry[-1].resource
    assert social_history_1.id is not None
    social_history_2 = summary.entry[-2].resource
    assert social_history_2.id is not None


def test_retrieve_patient_summary_social_history(mocker: MockerFixture) -> None:
    """The social history observations are validated and get the patient added as a subject."""
    with Path(__file__).parent.joinpath('fixtures').joinpath('patient.json').open(encoding='utf-8') as f:
        patient = Bundle.model_validate_json(f.read()).entry[0].resource

    with Path(__file__).parent.joinpath('fixtures', 'social_history.json').open() as f:
        social_history = json.load(f)

    assert 'subject' not in social_history[0]
    assert 'subject' not in social_history[1]

    mock_fhir_connector = mocker.Mock(spec=FHIRConnector)
    mock_fhir_connector.find_patient.return_value = patient
    mock_fhir_connector.patient_conditions.return_value = []
    mock_fhir_connector.patient_medication_requests.return_value = []
    mock_fhir_connector.patient_allergies.return_value = []
    mock_fhir_connector.patient_observations.return_value = []
    mock_fhir_connector.patient_immunizations.return_value = []
    mocker.patch('opal.services.fhir.utils.FHIRConnector', return_value=mock_fhir_connector)

    summary_json, summary_uuid = retrieve_patient_summary(
        settings=FHIR_SETTINGS, identifier='test-identifier', social_history=social_history
    )

    summary = Bundle.model_validate_json(summary_json)
    assert summary.identifier.value == summary_uuid

    social_history_1 = summary.entry[-1].resource
    assert social_history_1.id == social_history[1]['id']
    assert social_history_1.subject.reference == f'Patient/{patient.id}'
    social_history_2 = summary.entry[-2].resource
    assert social_history_2.id == social_history[0]['id']
    assert social_history_2.subject.reference == f'Patient/{patient.id}'


def test_retrieve_patient_summary_no_patient_error(mocker: MockerFixture) -> None:
    """An error is raised if the patient cannot be found."""
    mock_response: Mock = mocker.Mock(spec=requests.Response)
    mock_response.status_code = requests.codes.ok
    mock_response.json.return_value = []
    mock_session = mocker.Mock(spec=OAuth2Session)
    mock_session.get.return_value = mock_response
    mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

    with pytest.raises(FHIRDataRetrievalError, match='Error finding patient with identifier test-identifier'):
        retrieve_patient_summary(
            settings=FHIR_SETTINGS,
            identifier='test-identifier',
        )


def test_retrieve_patient_summary_patient_no_id(mocker: MockerFixture) -> None:
    """An error is raised if the patient does not have an ID."""
    with Path(__file__).parent.joinpath('fixtures').joinpath('patient.json').open(encoding='utf-8') as f:
        patient = Bundle.model_validate_json(f.read()).entry[0].resource

    patient.id = None

    mock_fhir_connector = mocker.Mock(spec=FHIRConnector)
    mock_fhir_connector.find_patient.return_value = patient
    mock_fhir_connector.patient_conditions.return_value = []
    mock_fhir_connector.patient_medication_requests.return_value = []
    mock_fhir_connector.patient_allergies.return_value = []
    mock_fhir_connector.patient_observations.return_value = []
    mock_fhir_connector.patient_immunizations.return_value = []
    mocker.patch('opal.services.fhir.utils.FHIRConnector', return_value=mock_fhir_connector)

    with pytest.raises(FHIRDataRetrievalError, match='Patient with identifier test-identifier has no ID'):
        retrieve_patient_summary(
            settings=FHIR_SETTINGS,
            identifier='test-identifier',
        )


def test_retrieve_patient_summary_oauth2_error(mocker: MockerFixture) -> None:
    """An error is raised if the OAuth2 authentication fails."""
    mock_session = mocker.Mock(spec=OAuth2Session)
    mock_session.fetch_token.side_effect = OAuth2Error('Invalid client credentials')
    mocker.patch('opal.services.fhir.fhir.OAuth2Session', return_value=mock_session)

    with pytest.raises(FHIRDataRetrievalError, match='Error retrieving data from FHIR server'):
        retrieve_patient_summary(
            settings=FHIR_SETTINGS,
            identifier='test-identifier',
        )
