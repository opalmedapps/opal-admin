# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions in this module provide the ability to communicate with other FHIR-enabled servers."""

import datetime as dt
from datetime import datetime

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

        self.session.fetch_token(token_endpoint)

    def find_patient(self, identifier: str) -> Patient:
        response = self.session.get(f'{self.fhir_url}/Patient?identifier={identifier}')
        response.raise_for_status()

        data = response.json()

        if 'entry' not in data or len(data['entry']) == 0:
            raise ValueError(f'No patient found with identifier {identifier}')

        if len(data['entry']) > 1:
            raise ValueError(f'Multiple patients found with identifier {identifier}')

        return Patient.model_validate(response.json()['entry'][0]['resource'])

    def patient_conditions(self, uuid: str) -> list[Condition]:
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
        response = self.session.get(f'{self.fhir_url}/MedicationRequest?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        medications_bundle = Bundle.model_validate(data)

        return [medication.resource for medication in medications_bundle.entry or []]

    def patient_allergies(self, uuid: str) -> list[AllergyIntolerance]:
        response = self.session.get(f'{self.fhir_url}/AllergyIntolerance?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        allergies_bundle = Bundle.model_validate(data)
        return [allergy.resource for allergy in allergies_bundle.entry or []]

    def patient_immunizations(self, uuid: str) -> list[Immunization]:
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
        response = self.session.get(f'{self.fhir_url}/Observation?patient={uuid}')
        response.raise_for_status()

        data = response.json()

        observations_bundle = Bundle.model_validate(data)
        return [observation.resource for observation in observations_bundle.entry or []]


if __name__ == '__main__':
    private_key = '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCEkJWEA6cOQldL\nNtKOmbJDyobgTP9SXXp4QheliowY7Bz78Q9SkZ98OJ+Q+Gd7C0YlgwcYgt4V2Tjd\ne5HNd0Y9cEwI5W9M6AIfjRi6uyYbdmL7ZX5vnDzgkMvz7d9OCSQpL3t4zCZSwmn2\nJqhpOBngxZmGHOx2x/uVbcIug6wPrT7lAJYHN+gCldqw0hNtsqq97q0FG7q90e0H\nveiudmTOF52YQ56y0QvKgMSkONPCpbg2t4+ubSB0OU/jFSPNz6W3Fo2NetbmTRso\n921wPerFg4GiGTT17mrbq8pcHCgVLrfNcB5uJcbkKZ3MRT2JBlhK7xj+w8OpjKll\nN++j2mCBAgMBAAECggEALy9DeMTQDnxAlA4Ebit4zzZkQaxGaOvK7skfn5Wr/ib0\nvhx0hsA8kzuYWEKCmsJNioaT3P6fzAkQe41DPW4J+05gUf5QWoBuWQqg1b5NdxLx\ncmgS0+k5pfkED2QIyr7oNxymhz2rGmQG0U27PhBw7ZeH6Luc0z6lZu+1YVcOxFku\nUE7lp1QIn9nAleM1pUOORb6/vQxAx693LfQyL5wpxT7BiSQgqG2ji7tuj/H6tUTv\n9apY490XABOy6nHQmaTKZJxhz45aGq41gmzj0upSLcxWuUWAgjhHvL9lGA3wTmL2\n6Qvb5yPbRoK4rf1WbUoNYfZvHVhkm3O94+wDHyyCUQKBgQD2DnG2fSm10TM3exH8\nruoQm9VOw5EGmaRGqUFoLHJBbAck6K6iRnVdi22/e1tGBuyZwj0Ls0Ytlrf4424/\nXIUrrJd6ifU3uS2JQdaMr1Ew3CPiWw70TpVabnsHog0+QM9Jf5jhjZj7712T43IH\nPW+EFbmsGPnxWYBcM6Rn0T5YtQKBgQCJ7AWP1GZG9S/BYe+A36C3F2NJV03dCyo6\nM2K+Vv4evIVGQnTHQdQ8G8UWcK/e+V7JPjqM9LA9cgwRQTR70Yg9g0LgAWFSecxO\nFcPpN450fHgDNviWD0GDeI76SQhQVoPq4qrQX4mYPU4Shw3J9cOY3nre3odZnivI\niekNuvmEHQKBgC//QU9Huwssc8Eu0KNpu17iBwoGPBP9hH4EJi4b/W2llP8uJGKj\nO+GzgQUJGxTd5OlZam8N2XKrI9f5BVh2w8NxN1s/7gWgqbFMln169WuChb1x5cji\nS2AIjRdAFTU/jy/XJAtbg6whVS+z/lpLMaWiV0Wq2Zaqzs8tg7R8rJzBAoGABuPd\nm0PXIDBbhGOqHVwOoVbvxNgxsZs/Ls0mX6/k3hA48Dudrd6iBaa1f9t9TbxTeeY7\n8pK+wzMRW0NQpebf0YLfMmWfQQmIpVX9BYea/ELDlBWI8aYtda3uJp7DZZAM4w0T\nz3kWXJ6jadWJYM+ASADFTqD7TgTS1x/cnqz6jhkCgYEAsciJEizxRB0SbVv/VQHy\nCr8OOIQmrD54c5yhGzVVQ+1za2Vz33Aih+UQHXw6vxwYCjQjBj+bxio8bipiS7dv\nDRdLJnS6aiRyz+r9l0K8fmWRpHUQLrxptfEDgJqYkXSCSh98d4oSr1TN9bJ8zdh0\nSYaG5jlvuQmyryBWBmFqISA=\n-----END PRIVATE KEY-----\n'
    test = FHIRConnector(
        oauth_url='https://openemr.opalmedapps.dev/oauth2/default',
        fhir_url='https://openemr.opalmedapps.dev/apis/default/fhir',
        client_id='BZWuvA5INTksQbPxqrrRSU_DMhlFjeP3yk_V9Qo9Q0o',
        private_key=private_key,
    )
    patient = test.find_patient('OBRR72061199')
    patient_uuid = patient.id
    conditions = test.patient_conditions(patient_uuid)
    medication_requests = test.patient_medication_requests(patient_uuid)
    allergies = test.patient_allergies(patient_uuid)
    observations = test.patient_observations(patient_uuid)
    immunizations = test.patient_immunizations(patient_uuid)

    from . import ips

    ips_bundle = ips.build_patient_summary(
        patient, conditions, medication_requests, allergies, observations, immunizations
    )
    print(ips_bundle.model_dump_json(indent=2))
