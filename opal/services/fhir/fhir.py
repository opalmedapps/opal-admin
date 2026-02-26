# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions in this module provide the ability to communicate with other FHIR-enabled servers."""

import datetime as dt
from datetime import datetime
from typing import Any, cast

import structlog
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7523 import PrivateKeyJWT
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.patient import Patient

SCOPES = [
    'system/Patient.read',
    'system/Condition.read',
    'system/MedicationRequest.read',
    'system/AllergyIntolerance.read',
    'system/Observation.read',
    'system/Immunization.read',
    'system/DiagnosticReport.read',
]
LOGGER = structlog.get_logger(__name__)


class PatientNotFoundError(Exception):
    """Raised when a patient is not found in the FHIR server."""

    pass


class MultiplePatientsFoundError(Exception):
    """Raised when multiple patients are found for a given identifier in the FHIR server."""

    pass


def _clean_coding(coding: dict[str, Any]) -> None:
    """Clean a coding code by stripping whitespace and trailing periods."""
    # strip whitespace from code fields to avoid validation errors
    coding['code'] = coding['code'].rstrip()
    # strip trailing period which is an invalid code
    coding['code'] = coding['code'].rstrip('.')
    # replace empty code display fields to avoid validation errors
    coding['display'] = coding['display'] or 'No display provided'


class FHIRConnector:
    """
    A FHIR connector to interact with a FHIR server using OAuth2 authentication.

    The authentication method used is the client credentials grant.

    See: https://www.hl7.org/fhir/smart-app-launch/backend-services.html
    """

    def __init__(self, oauth_url: str, fhir_url: str, client_id: str, private_key: str):
        """
        Initialize the FHIR connector and fetch the authentication token.

        Args:
            oauth_url: OAuth2 base URL
            fhir_url: FHIR API base URL
            client_id: OAuth2 client ID
            private_key: Private key in PEM format for PrivateKeyJWT authentication
        """
        self.fhir_url = fhir_url
        token_endpoint = f'{oauth_url}/token'

        self.session = OAuth2Session(
            client_id=client_id,
            client_secret=private_key,
            scope=SCOPES,
            token_endpoint_auth_method=PrivateKeyJWT(
                token_endpoint=token_endpoint,
                alg='RS384',
            ),
        )

        LOGGER.debug('Fetching new token from OAuth URL at %s', token_endpoint)

        self.session.fetch_token(token_endpoint)

        LOGGER.debug('Successfully fetched new token', extra=self.session.token)

    def find_patient(self, identifier: str) -> Patient:
        """
        Find a patient by their identifier.

        The identifier is usually the health insurance number.

        Args:
            identifier: the patient identifier

        Returns:
            Patient resource.

        Raises:
            PatientNotFoundError: If no patient is found for the given identifier
            MultiplePatientsFoundError: If multiple patients are found for the given identifier
        """
        LOGGER.debug('Searching for patient with identifier %s', identifier)

        response = self.session.get(f'{self.fhir_url}/Patient?identifier={identifier}')
        response.raise_for_status()

        data = response.json()

        if 'entry' not in data or len(data['entry']) == 0:
            raise PatientNotFoundError(f'No patient found with identifier {identifier}')

        if len(data['entry']) > 1:
            raise MultiplePatientsFoundError(f'Multiple patients found with identifier {identifier}')

        return Patient.model_validate(response.json()['entry'][0]['resource'])

    def patient_conditions(self, uuid: str) -> list[Condition]:
        """
        Retrieve all conditions for a patient.

        Args:
            uuid: the UUID of the patient

        Returns:
            the list of Condition resources
        """
        LOGGER.debug('Retrieving conditions for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/Condition?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        # sanitize some known data issues
        # these should eventually be fixed at the source
        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            for coding in resource.get('code', {}).get('coding', []):
                _clean_coding(coding)

        conditions_bundle = Bundle.model_validate(data)
        return [
            cast('Condition', condition.resource) for condition in conditions_bundle.entry or [] if condition.resource
        ]

    def patient_medication_requests(self, uuid: str) -> list[MedicationRequest]:
        """
        Retrieve all medication requests for a patient.

        Args:
            uuid: the UUID of the patient

        Returns:
            the list of MedicationRequest resources
        """
        LOGGER.debug('Retrieving medication requests for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/MedicationRequest?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        medications_bundle = Bundle.model_validate(data)

        return [
            cast('MedicationRequest', medication.resource)
            for medication in medications_bundle.entry or []
            if medication.resource
        ]

    def patient_allergies(self, uuid: str) -> list[AllergyIntolerance]:
        """
        Retrieve all allergies for a patient.

        Args:
            uuid: the UUID of the patient

        Returns:
            the list of AllergyIntolerance resources
        """
        LOGGER.debug('Retrieving allergies for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/AllergyIntolerance?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        # sanitize some known data issues
        # these should eventually be fixed at the source
        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            for coding in resource.get('code', {}).get('coding', []):
                _clean_coding(coding)

        allergies_bundle = Bundle.model_validate(data)
        return [
            cast('AllergyIntolerance', allergy.resource) for allergy in allergies_bundle.entry or [] if allergy.resource
        ]

    def patient_immunizations(self, uuid: str) -> list[Immunization]:
        """
        Retrieve all immunizations for a patient.

        Args:
            uuid: the UUID of the patient

        Returns:
            the list of Immunization resources
        """
        LOGGER.debug('Retrieving immunizations for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/Immunization?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            if 'meta' in resource and 'lastUpdated' in resource['meta']:  # pragma: no cover
                # sanitize invalid dates, assume that '-0001' means last year
                # this should eventually be fixed at the source
                resource['meta']['lastUpdated'] = resource['meta']['lastUpdated'].replace(
                    '-0001', str(datetime.now(tz=dt.UTC).year - 1)
                )

        immunizations_bundle = Bundle.model_validate(data)

        return [
            cast('Immunization', immunization.resource)
            for immunization in immunizations_bundle.entry or []
            if immunization.resource
        ]

    def patient_observations(self, uuid: str) -> list[Observation]:
        """
        Retrieve all observations for a patient.

        Args:
            uuid: the UUID of the patient

        Returns:
            the list of Observation resources
        """
        LOGGER.debug('Retrieving observations for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/Observation?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        observations_bundle = Bundle.model_validate(data)
        return [
            cast('Observation', observation.resource)
            for observation in observations_bundle.entry or []
            if observation.resource
        ]
