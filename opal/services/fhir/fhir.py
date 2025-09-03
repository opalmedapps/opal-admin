# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions in this module provide the ability to communicate with other FHIR-enabled servers."""

import datetime as dt
from datetime import datetime

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


class FHIRConnector:
    def __init__(self, oauth_url: str, fhir_url: str, client_id: str, private_key: str):
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
        LOGGER.debug('Searching for patient with identifier %s', identifier)

        response = self.session.get(f'{self.fhir_url}/Patient?identifier={identifier}')
        response.raise_for_status()

        data = response.json()

        if 'entry' not in data or len(data['entry']) == 0:
            raise ValueError(f'No patient found with identifier {identifier}')

        if len(data['entry']) > 1:
            raise ValueError(f'Multiple patients found with identifier {identifier}')

        return Patient.model_validate(response.json()['entry'][0]['resource'])

    def patient_conditions(self, uuid: str) -> list[Condition]:
        LOGGER.debug('Retrieving conditions for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/Condition?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        # sanitize some known data issues
        # these should eventually be fixed at the source
        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            if 'code' in resource:
                for coding in resource['code'].get('coding', []):
                    # strip whitespace from code fields to avoid validation errors
                    coding['code'] = coding['code'].rstrip()
                    # replace empty code display fields to avoid validation errors
                    coding['display'] = coding['display'] or 'No display provided'

        conditions_bundle = Bundle.model_validate(data)
        return [condition.resource for condition in conditions_bundle.entry or []]

    def patient_medication_requests(self, uuid: str) -> list[MedicationRequest]:
        LOGGER.debug('Retrieving medication requests for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/MedicationRequest?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        medications_bundle = Bundle.model_validate(data)

        return [medication.resource for medication in medications_bundle.entry or []]

    def patient_allergies(self, uuid: str) -> list[AllergyIntolerance]:
        LOGGER.debug('Retrieving allergies for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/AllergyIntolerance?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        allergies_bundle = Bundle.model_validate(data)
        return [allergy.resource for allergy in allergies_bundle.entry or []]

    def patient_immunizations(self, uuid: str) -> list[Immunization]:
        LOGGER.debug('Retrieving immunizations for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/Immunization?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            if 'meta' in resource and 'lastUpdated' in resource['meta']:
                # sanitize invalid dates
                resource['meta']['lastUpdated'] = resource['meta']['lastUpdated'].replace(
                    '-0001', str(datetime.now(tz=dt.UTC).year - 1)
                )

        immunizations_bundle = Bundle.model_validate(data)

        return [immunization.resource for immunization in immunizations_bundle.entry or []]

    def patient_observations(self, uuid: str) -> list[Observation]:
        LOGGER.debug('Retrieving observations for patient with UUID %s', uuid)

        response = self.session.get(f'{self.fhir_url}/Observation?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        observations_bundle = Bundle.model_validate(data)
        return [observation.resource for observation in observations_bundle.entry or []]
