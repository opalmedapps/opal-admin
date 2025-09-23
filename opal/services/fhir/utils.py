# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utility functions for FHIR functionality, including building patient summaries and JWE encryption."""

import secrets

import structlog
from jose import jwe, utils

from . import ips
from .fhir import FHIRConnector

LOGGER = structlog.get_logger(__name__)


# https://docs.smarthealthit.org/smart-health-links/spec/#encrypting-and-decrypting-files
def jwe_sh_link_encrypt(data: str) -> tuple[str, bytes]:
    """
    Encrypt data using JWE for SMART Health Links.

    Args:
        data: the data to encrypt

    Returns:
        a tuple of the encryption key (as a URL-safe base64 string) and the encrypted data (as bytes)
    """
    # generate key with 32 bytes of randomness
    key = secrets.token_urlsafe(32)
    # base64 URL decode to have 32 bytes of data
    key_decoded = utils.base64url_decode(key.encode('utf-8'))

    encrypted = jwe.encrypt(data, key_decoded, algorithm='dir', encryption='A256GCM', cty='application/fhir+json')

    return (key, encrypted)


def retrieve_patient_summary(oauth_url: str, fhir_url: str, client_id: str, private_key: str, identifier: str) -> str:
    """
    Retrieve patient data and build a patient summary in IPS format for a patient identified by their identifier.

    Args:
        oauth_url: OAuth2 base URL
        fhir_url: FHIR API base URL
        client_id: OAuth2 client ID
        private_key: Private key in PEM format for PrivateKeyJWT authentication
        identifier: the patient identifier (usually the health insurance number)

    Returns:
        the patient summary in IPS format as a JSON string
    """
    LOGGER.debug(
        'Building patient summary for patient with identifier %s, using OAuth2 URL: %s, FHIR API: %s, client ID: %s',
        identifier,
        oauth_url,
        fhir_url,
        client_id,
    )
    fhir = FHIRConnector(
        oauth_url=oauth_url,
        fhir_url=fhir_url,
        client_id=client_id,
        private_key=private_key,
    )
    patient = fhir.find_patient(identifier)
    patient_uuid = patient.id
    conditions = fhir.patient_conditions(patient_uuid)
    medication_requests = fhir.patient_medication_requests(patient_uuid)
    allergies = fhir.patient_allergies(patient_uuid)
    observations = fhir.patient_observations(patient_uuid)
    immunizations = fhir.patient_immunizations(patient_uuid)

    LOGGER.debug(
        'Retrieved data for patient %s: %d conditions, %d medication requests, %d allergies, %d observations, %d immunizations',
        patient_uuid,
        len(conditions),
        len(medication_requests),
        len(allergies),
        len(observations),
        len(immunizations),
    )

    LOGGER.debug('Building IPS bundle for patient with UUID %s', patient_uuid)

    ips_bundle = ips.build_patient_summary(
        patient, conditions, medication_requests, allergies, observations, immunizations
    )

    LOGGER.debug('Successfully built IPS bundle for patient with UUID %s', patient_uuid)

    return ips_bundle.model_dump_json(indent=2)  # type: ignore[no-any-return]
