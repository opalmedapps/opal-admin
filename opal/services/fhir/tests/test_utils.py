# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64
import json
from pathlib import Path

from fhir.resources.R4B.bundle import Bundle
from jose import jwe, utils
from pytest_mock import MockerFixture

from opal.services.fhir.fhir import FHIRConnector
from opal.services.fhir.utils import jwe_sh_link_encrypt, retrieve_patient_summary


def test_jwe_sh_link_encrypt() -> None:
    """The encrypted data can be decrypted correctly."""
    data = 'secret data'
    key, encrypted = jwe_sh_link_encrypt(data)

    # Key should be exactly 43 characters (32 bytes of randomness -> base64 encoded without padding)
    assert len(key) == 43, f'Key length is {len(key)}, expected 43 characters'

    key_decoded = utils.base64url_decode(key.encode('utf-8'))
    decrypted = jwe.decrypt(encrypted, key_decoded).decode('utf-8')

    assert decrypted == data


def test_jwe_sh_link_encrypt_empty() -> None:
    """Empty encrypted data can be encrypted and decrypted correctly."""
    data = ''
    key, encrypted = jwe_sh_link_encrypt(data)

    key_decoded = utils.base64url_decode(key.encode('utf-8'))
    decrypted = jwe.decrypt(encrypted, key_decoded).decode('utf-8')

    assert decrypted == data


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

    summary_json = retrieve_patient_summary(
        oauth_url='https://example.com/oauth2',
        fhir_url='https://example.com/fhir',
        client_id='test-client-id',
        private_key='private-key',
        identifier='test-identifier',
    )

    Bundle.model_validate_json(summary_json)
