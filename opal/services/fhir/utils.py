# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utility functions for FHIR functionality, including building patient summaries and JWE encryption."""

import logging
import secrets
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import structlog
from authlib.oauth2 import OAuth2Error
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.reference import Reference
from jose import jwe, utils
from pydantic_core import PydanticCustomError, ValidationError
from requests import RequestException

from . import ips
from .fhir import FHIRConnector, MultiplePatientsFoundError, PatientNotFoundError

LOGGER: logging.Logger = structlog.get_logger(__name__)


class FHIRDataRetrievalError(Exception):
    """Raised when there is an error retrieving data from the FHIR server."""

    pass


@dataclass
class FHIRConnectionSettings:
    """
    Settings for connecting to a FHIR server via OAuth2.

    - oauth_url: OAuth2 base URL
    - fhir_url: FHIR API base URL
    - client_id: OAuth2 client ID
    - private_key: Private key in PEM format for PrivateKeyJWT authentication
    """

    oauth_url: str
    fhir_url: str
    client_id: str
    private_key: str


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


def retrieve_patient_summary(
    settings: FHIRConnectionSettings,
    identifier: str,
    social_history: Sequence[dict[str, Any]] = (),
) -> tuple[str, str]:
    """
    Retrieve patient data and build a patient summary in IPS format for a patient identified by their identifier.

    Args:
        settings: the settings to use for connecting to the FHIR server
        identifier: the patient identifier (usually the health insurance number)
        social_history: optional social history data to include in the IPS bundle, for example, patient-reported alcohol and tobacco use

    Returns:
        a tuple of the patient summary in IPS format as a JSON string and the UUID of the IPS bundle

    Raises:
        FHIRDataRetrievalError: if there is an error retrieving data from the FHIR server
    """
    LOGGER.debug(
        'Building patient summary for patient with identifier %s, using OAuth2 URL: %s, FHIR API: %s, client ID: %s',
        identifier,
        settings.oauth_url,
        settings.fhir_url,
        settings.client_id,
    )

    try:
        fhir = FHIRConnector(
            oauth_url=settings.oauth_url,
            fhir_url=settings.fhir_url,
            client_id=settings.client_id,
            private_key=settings.private_key,
        )

        patient = fhir.find_patient(identifier)
        patient_uuid = patient.id

        if not patient_uuid:
            raise FHIRDataRetrievalError(f'Patient with identifier {identifier} has no ID')

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

        social_history_observations = []
        social_history_errors: list[ValidationError] = []
        for social_history_item in social_history:
            try:
                observation = validate_observation(social_history_item)
            except ValidationError as exc:
                social_history_errors.append(exc)
            else:
                observation.subject = Reference(reference=f'Patient/{patient_uuid}', type='Patient')
                social_history_observations.append(observation)
    except (PatientNotFoundError, MultiplePatientsFoundError) as exc:
        LOGGER.exception('Error finding patient with identifier %s', identifier)
        raise FHIRDataRetrievalError(f'Error finding patient with identifier {identifier}') from exc
    except (RequestException, OAuth2Error) as exc:
        LOGGER.exception('Error retrieving data from FHIR server')
        raise FHIRDataRetrievalError('Error retrieving data from FHIR server') from exc
    else:
        if social_history_errors:
            LOGGER.error(
                'Error validating social history observations', extra={'validation_errors': social_history_errors}
            )
            raise FHIRDataRetrievalError('Error validating social history observations')

        LOGGER.debug('Building IPS bundle for patient with UUID %s', patient_uuid)

        ips_bundle = ips.build_patient_summary(
            patient,
            conditions,
            medication_requests,
            allergies,
            observations,
            immunizations,
            social_history=social_history_observations,
        )

        LOGGER.debug('Successfully built IPS bundle for patient with UUID %s', patient_uuid)

        # we know that there is an identifier because it is set in the build_patient_summary function
        ips_uuid: str = ips_bundle.identifier.value  # type: ignore[assignment,union-attr]

        return ips_bundle.model_dump_json(indent=2), ips_uuid


def validate_observation(value: dict[str, Any]) -> Observation:
    """
    Validate that a dictionary is a valid FHIR `Observation` resource.

    If the observation is missing an `id`, one will be generated and added to the observation.

    Raises a Pydantic `ValidationError` if the value is not a valid `Observation`.

    Args:
        value: the value to validate

    Returns:
        the validated observation if it is valid

    Raises:
        ValidationError: if the value is not a valid `Observation`
    """  # noqa: DOC501, DOC502
    observation = Observation.model_validate(value)

    if observation.id is None:
        observation.id = str(uuid.uuid4())

    if observation.subject is not None:
        raise ValidationError.from_exception_data(
            title='Observation',
            line_errors=[
                {
                    'type': PydanticCustomError(
                        'subject_forbidden',
                        'subject cannot be set manually, it is assigned automatically when building the patient summary',
                    ),
                    'loc': ('subject',),
                    'input': observation.subject.model_dump(),
                }
            ],
        )

    return observation
