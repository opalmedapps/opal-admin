# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions in this module provide the ability to communicate with other FHIR-enabled servers."""

import datetime as dt
import json  # noqa: F401, RUF100
import uuid
from pathlib import Path  # noqa: F401, RUF100

from django.conf import settings

import requests  # noqa: F401, RUF100
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.composition import Composition, CompositionSection
from fhir.resources.R4B.device import Device, DeviceDeviceName
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.narrative import Narrative
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.reference import Reference
from jose import jwe, utils
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session


class FhirCommunication:
    """Class that manages interactions with a FHIR server."""

    def __init__(self, server_type: str):
        """Constructor."""
        self.oauth = None
        self.debug = True

        if server_type == 'OpenEMR':
            if settings.OPENEMR_ENABLED:
                self.client_id = settings.OPENEMR_CLIENT_ID
                self.oauth_url = settings.OPENEMR_OAUTH_URL
                self.username = settings.OPENEMR_USERNAME
                self.password = settings.OPENEMR_PASSWORD
                self.fhir_url = settings.OPENEMR_FHIR_URL
            else:
                raise NotImplementedError("FhirCommunication can't be instantiated for OpenEMR, because OpenEMR isn't enabled")
        else:
            raise NotImplementedError(f'FhirCommunication server type not implemented: {server_type}')

    def connect(self):
        """TODO"""
        scopes = [
            # to get a refresh token
            'offline_access',
            'user/Patient.read',
            'user/Condition.read',
            'user/MedicationRequest.read',
            'user/AllergyIntolerance.read',
            'user/Observation.read',
            'user/Immunization.read',
            'user/DiagnosticReport.read',
        ]

        self.oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.client_id, refresh_token=''))
        self.oauth.fetch_token(
            token_url=f'{self.oauth_url}/token',
            username=self.username,
            password=self.password,
            client_id=self.client_id,
            user_role='users',
            scope=' '.join(scopes),
        )

        self.oauth.get(f'{self.fhir_url}/metadata')

    def assemble_ips(self, ramq: str):
        patient_bundle = self.get_patient(ramq)
        patient_uuid = patient_bundle['entry'][0]['resource']['id']
        conditions_bundle = self.get_conditions(patient_uuid)
        medication_requests_bundle = self.get_medication_requests(patient_uuid)
        allergies_bundle = self.get_allergies(patient_uuid)
        observations_bundle = self.get_observations(patient_uuid)
        immunizations_bundle = self.get_immunizations(patient_uuid)

        patient_bundle = Bundle.model_validate(patient_bundle)
        patient: Patient = patient_bundle.entry[0].resource

        if self.debug:
            print(f'Patient: {patient.name[0].family} {patient.name[0].given[0]} ({patient.id})')

        conditions_bundle = Bundle.model_validate(conditions_bundle)
        conditions = [condition.resource for condition in conditions_bundle.entry] if conditions_bundle.entry else []

        medication_requests_bundle = Bundle.model_validate(medication_requests_bundle)
        medication_requests = [
            medication_request.resource
            for medication_request in medication_requests_bundle.entry
            if medication_request.resource.subject.reference == f'Patient/{patient.id}'
        ] if medication_requests_bundle.entry else []

        allergies_bundle = Bundle.model_validate(allergies_bundle)
        allergies = [allergy.resource for allergy in allergies_bundle.entry] if allergies_bundle.entry else []

        observations_bundle = Bundle.model_validate(observations_bundle)
        vital_signs = [
            observation.resource
            for observation in observations_bundle.entry
            if observation.resource.category[0].coding[0].code == 'vital-signs'
        ] if observations_bundle.entry else []
        labs = [
            observation.resource
            for observation in observations_bundle.entry
            if observation.resource.category[0].coding[0].code == 'laboratory'
        ] if observations_bundle.entry else []

        # For some reason does not validate with Bundle, even when it is the R4B bundle
        # immunizations_bundle = Bundle.model_validate(immunizations_bundle)
        immunizations = [] if immunizations_bundle['total'] == 0 else [
            Immunization.model_validate(immunization['resource']) for immunization in immunizations_bundle['entry']
        ]

        generator = Device(
            id=f'{uuid.uuid4()}',
            manufacturer='Opal Health Informatics Group',
            deviceName=[DeviceDeviceName(name='Opal IPS Generator', type='user-friendly-name')],
        )

        composition = Composition(
            id=f'{uuid.uuid4()}',
            status='final',
            type=CodeableConcept(
                coding=[Coding(system='http://loinc.org', code='60591-5', display='Patient summary document')],
            ),
            author=[Reference(reference=f'urn:uuid:{generator.id}')],
            date=dt.datetime.now(tz=dt.UTC).replace(microsecond=0),
            title='International Patient Summary',
            subject=Reference(reference=f'urn:uuid:{patient.id}'),
            section=[
                CompositionSection(
                    title='Active Problems',
                    code=CodeableConcept(
                        coding=[Coding(system='http://loinc.org', code='11450-4', display='Problem list reported')]
                    ),
                    entry=[
                        Reference(reference=f'urn:uuid:{condition.id}')
                        for condition in conditions
                        if condition.clinicalStatus.coding[0].code == 'active'
                    ],
                ),
                CompositionSection(
                    title='Past Medical History',
                    code=CodeableConcept(
                        coding=[Coding(system='http://loinc.org', code='11348-0',
                                       display='History of Past illness Narrative')]
                    ),
                    entry=[
                        Reference(reference=f'Condition/{condition.id}')
                        for condition in conditions
                        if condition.clinicalStatus.coding[0].code != 'active'
                    ],
                ),
                CompositionSection(
                    title='Medication',
                    code=CodeableConcept(
                        coding=[
                            Coding(system='http://loinc.org', code='10160-0',
                                   display='History of Medication use Narrative')
                        ],
                    ),
                    entry=[
                        Reference(reference=f'urn:uuid:{medication_request.id}') for medication_request in
                        medication_requests
                    ],
                ),
                CompositionSection(
                    title='Allergies and Intolerances',
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system='http://loinc.org', code='48765-2',
                                display='Allergies and adverse reactions Document'
                            )
                        ]
                    ),
                    entry=[Reference(reference=f'urn:uuid:{allergy.id}') for allergy in allergies],
                ),
                CompositionSection(
                    title='Vital Signs',
                    code=CodeableConcept(
                        coding=[Coding(system='http://loinc.org', code='8716-3', display='Vital signs')]),
                    entry=[Reference(reference=f'urn:uuid:{vital_sign.id}') for vital_sign in vital_signs],
                ),
                CompositionSection(
                    title='Laboratory Results',
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system='http://loinc.org',
                                code='30954-2',
                                display='Relevant diagnostic tests/laboratory data Narrative',
                            )
                        ]
                    ),
                    entry=[Reference(reference=f'urn:uuid:{lab.id}') for lab in labs],
                ),
                CompositionSection(
                    title='Immunizations',
                    code=CodeableConcept(
                        coding=[Coding(system='http://loinc.org', code='11369-6',
                                       display='History of Immunization Narrative')]
                    ),
                    entry=[Reference(reference=f'urn:uuid:{immunization.id}') for immunization in immunizations],
                ),
            ],
        )

        ips = Bundle(
            identifier={'system': 'urn:oid:2.16.724.4.8.10.200.10', 'value': f'{uuid.uuid4()}'},
            type='document',
            timestamp=dt.datetime.now(tz=dt.UTC).replace(microsecond=0),
            entry=[
                BundleEntry(resource=composition, fullUrl=f'urn:uuid:{composition.id}'),
                BundleEntry(resource=patient, fullUrl=f'urn:uuid:{patient.id}'),
                BundleEntry(resource=generator, fullUrl=f'urn:uuid:{generator.id}'),
            ],
        )

        ips.entry.extend(
            BundleEntry(resource=condition, fullUrl=f'urn:uuid:{condition.id}') for condition in conditions)
        ips.entry.extend(BundleEntry(resource=allergy, fullUrl=f'urn:uuid:{allergy.id}') for allergy in allergies)
        ips.entry.extend(
            BundleEntry(resource=medication_request, fullUrl=f'urn:uuid:{medication_request.id}')
            for medication_request in medication_requests
        )
        ips.entry.extend(
            BundleEntry(resource=vital_sign, fullUrl=f'urn:uuid:{vital_sign.id}') for vital_sign in vital_signs)
        ips.entry.extend(BundleEntry(resource=lab, fullUrl=f'urn:uuid:{lab.id}') for lab in labs)
        ips.entry.extend(
            BundleEntry(resource=immunization, fullUrl=f'urn:uuid:{immunization.id}') for immunization in immunizations
        )

        # add narrative for empty entries
        for section in composition.section:
            if not section.entry:
                section.text = Narrative(
                    status='generated',
                    div=f'<div xmlns="http://www.w3.org/1999/xhtml">There is no information available about the subject\'s {section.title.lower()}.</div>',
                )
                section.entry = None

        formatted_ips = ips.model_dump_json(indent=2)
        print(formatted_ips)
        return formatted_ips

    # TODO move to a different service?
    def encrypt_shlink_file(self, contents, key):
        key_bytes = utils.base64url_decode(key)
        return jwe.encrypt(contents, key_bytes, algorithm='dir', encryption='A256GCM', cty='application/fhir+json')

    def get_patient(self, ramq: str):
        response = self.oauth.get(f'{self.fhir_url}/Patient?identifier={ramq}').json()
        patient = response['entry'][0]['resource']

        if self.debug:
            print(f'Patient: UUID={patient['id']}, Name={patient["name"][0]["family"]}, {patient["name"][0]["given"][0]}')

        return response

    def get_conditions(self, uuid):
        response = self.oauth.get(f'{self.fhir_url}/Condition?patient={uuid}').json()
        self.strip_whitespace(response)
        self.sanitize_empty_strings(response)

        if self.debug:
            print(f'Conditions: {response['total']}')
            for condition in response['entry']:
                print(f'Condition: "{condition["resource"]["code"]["coding"][0]["code"]}"')

        return response

    def get_medication_requests(self, uuid):
        response = self.oauth.get(f'{self.fhir_url}/MedicationRequest?patient={uuid}').json()

        if self.debug:
            print(f'MedicationRequests: {response["total"]}')

        return response

    def get_allergies(self, uuid):
        response = self.oauth.get(f'{self.fhir_url}/AllergyIntolerance?patient={uuid}').json()

        if self.debug:
            print(f'Allergies: {response["total"]}')

        return response

    def get_observations(self, uuid):
        response = self.oauth.get(f'{self.fhir_url}/Observation?patient={uuid}').json()

        print(f'Observations: {response["total"]}')

        return response

    def get_immunizations(self, uuid):
        response = self.oauth.get(f'{self.fhir_url}/Immunization?patient={uuid}').json()
        self.sanitize_invalid_dates(response)

        print(f'Immunizations: {response["total"]}')

        return response

    def strip_whitespace(self, item):
        if type(item) is dict:
            for key, value in item.items():
                if key == 'code' and type(value) is str:
                    item[key] = value.strip()
                else:
                    self.strip_whitespace(item[key])
        elif type(item) is list:
            for x in item:
                self.strip_whitespace(x)

    # Validation error for Immunization
    # meta.lastUpdated - Input should be a valid datetime or date, invalid character in year [type=datetime_from_date_parsing, input_value='-0001-11-30T00:00:00-04:00', input_type=str]
    def sanitize_invalid_dates(self, item):
        if type(item) is dict:
            for key, value in item.items():
                if key == 'lastUpdated' and type(value) is str:
                    item[key] = value.replace('-0001', '1900')
                else:
                    self.sanitize_invalid_dates(item[key])
        elif type(item) is list:
            for x in item:
                self.sanitize_invalid_dates(x)

    # Validation error for Condition Bundle
    # entry.0.resource.code.coding.0.display - String should match pattern '[\S]+' [type=string_pattern_mismatch, input_value='', input_type=str]
    def sanitize_empty_strings(self, item):
        if type(item) is dict:
            for key, value in list(item.items()):
                if type(value) is str and not value:
                    # Remove keys that have empty string values
                    item.pop(key)
                else:
                    self.sanitize_empty_strings(item[key])
        elif type(item) is list:
            for x in item:
                self.sanitize_empty_strings(x)
