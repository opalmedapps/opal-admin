# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from pathlib import Path
from typing import Any

from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.patient import Patient

from opal.services.fhir import ips


def _load_fixture(filename: str) -> dict[str, Any]:
    with Path(__file__).parent.joinpath('fixtures').joinpath(filename).open(encoding='utf-8') as f:
        data: dict[str, Any] = json.load(f)
        return data


def _prepare_build_patient_summary() -> tuple[
    Bundle,
    Patient,
    list[Condition],
    list[MedicationRequest],
    list[AllergyIntolerance],
    list[Observation],
    list[Immunization],
]:
    patient_data = _load_fixture('patient.json')
    patient = Bundle.model_validate(patient_data).entry[0].resource

    condition_data = _load_fixture('conditions.json')
    conditions_bundle = Bundle.model_validate(condition_data)
    conditions = [condition.resource for condition in conditions_bundle.entry]

    medication_request_data = _load_fixture('medication_requests.json')
    medication_requests_bundle = Bundle.model_validate(medication_request_data)
    medication_requests = [medication_request.resource for medication_request in medication_requests_bundle.entry]

    allergy_data = _load_fixture('allergies.json')
    allergies_bundle = Bundle.model_validate(allergy_data)
    allergies = [allergy.resource for allergy in allergies_bundle.entry]

    observation_data = _load_fixture('observations.json')
    observations_bundle = Bundle.model_validate(observation_data)
    observations = [observation.resource for observation in observations_bundle.entry]

    immunization_data = _load_fixture('immunizations.json')
    immunizations_bundle = Bundle.model_validate(immunization_data)
    immunizations = [immunization.resource for immunization in immunizations_bundle.entry]

    summary = ips.build_patient_summary(
        patient,
        conditions,
        medication_requests,
        allergies,
        observations,
        immunizations,
    )

    return (summary, patient, conditions, medication_requests, allergies, observations, immunizations)


def test_build_patient_summary() -> None:
    """A patient summary can be built correctly."""
    summary, _patient, conditions, medication_requests, allergies, observations, immunizations = (
        _prepare_build_patient_summary()
    )

    Bundle.model_validate(summary.model_dump())

    assert summary.type == 'document'
    assert summary.identifier.system == 'urn:oid:2.16.724.4.8.10.200.10'

    # Composition, Patient, Device and the resources
    assert len(summary.entry) == (
        3 + len(conditions) + len(medication_requests) + len(allergies) + len(observations) + len(immunizations)
    )


def test_build_patient_summary_composition() -> None:
    """The Composition resource in the patient summary is built correctly."""
    summary, _patient, conditions, medication_requests, allergies, observations, immunizations = (
        _prepare_build_patient_summary()
    )

    composition = summary.entry[0].resource
    assert composition.__resource_type__ == 'Composition'
    assert 'International Patient Summary as of' in composition.title
    assert composition.type.coding[0].display == 'Patient summary document'
    assert composition.type.coding[0].code == '60591-5'

    # Verify all 7 IPS sections
    assert len(composition.section) == 7

    vital_signs = [
        observation for observation in observations if observation.category[0].coding[0].code == 'vital-signs'
    ]
    labs = [observation for observation in observations if observation.category[0].coding[0].code == 'laboratory']

    expected_sections = [
        # The second condition is still active
        ('Active Problems', '11450-4', conditions[1:]),
        # The first condition is in remission
        ('Past Medical History', '11348-0', conditions[:1]),
        ('Medication', '10160-0', medication_requests),
        ('Allergies and Intolerances', '48765-2', allergies),
        ('Vital Signs', '8716-3', vital_signs),
        ('Laboratory Results', '30954-2', labs),
        ('Immunizations', '11369-6', immunizations),
    ]

    for section, (expected_title, expected_code, resources) in zip(composition.section, expected_sections, strict=True):
        # The expected section is there
        assert section.title == expected_title
        assert section.code.coding[0].code == expected_code
        assert section.code.coding[0].system == 'http://loinc.org'

        # The section's resources are referenced
        if resources:
            assert len(section.entry) == len(resources)
            for entry, resource in zip(section.entry, resources, strict=True):
                assert entry.reference == f'urn:uuid:{resource.id}', (
                    f'Section {section.title} has an incorrect resource reference'
                )
        else:
            assert section.entry is None


def test_build_patient_summary_empty_sections() -> None:
    """Sections with no resources have a narrative indicating no information is available."""
    patient_data = _load_fixture('patient.json')
    patient = Bundle.model_validate(patient_data).entry[0].resource

    summary = ips.build_patient_summary(patient, [], [], [], [], [])

    composition = summary.entry[0].resource

    for section in composition.section:
        assert section.entry is None
        assert "There is no information available about the subject's" in section.text.div


def test_build_patient_summary_patient() -> None:
    """The patient is included."""
    patient_data = _load_fixture('patient.json')
    patient = Bundle.model_validate(patient_data).entry[0].resource

    summary = ips.build_patient_summary(patient, [], [], [], [], [])

    composition = summary.entry[0].resource

    assert composition.subject.reference == f'urn:uuid:{patient.id}'

    patient_entry = summary.entry[1]
    assert patient_entry.resource.__resource_type__ == 'Patient'
    assert patient_entry.resource.id == patient.id
    assert patient_entry.fullUrl == f'urn:uuid:{patient.id}'


def test_build_patient_summary_generator() -> None:
    """The generator is included."""
    patient_data = _load_fixture('patient.json')
    patient = Bundle.model_validate(patient_data).entry[0].resource

    summary = ips.build_patient_summary(patient, [], [], [], [], [])

    composition = summary.entry[0].resource
    generator = summary.entry[2].resource

    assert len(composition.author) == 1
    assert composition.author[0].reference == f'urn:uuid:{generator.id}'

    assert generator.__resource_type__ == 'Device'
    assert generator.deviceName[0].type == 'user-friendly-name'


def test_build_patient_summary_resources_included() -> None:
    """All resources are included in the patient summary Bundle."""
    summary, _patient, conditions, medication_requests, allergies, observations, immunizations = (
        _prepare_build_patient_summary()
    )

    # Skip the first three entries (Composition, Patient, Device)
    resource_ids = {entry.resource.id for entry in summary.entry[3:]}

    expected_ids: set[str] = set()
    expected_ids.update(condition.id for condition in conditions)
    expected_ids.update(medication_request.id for medication_request in medication_requests)
    expected_ids.update(allergy.id for allergy in allergies)
    expected_ids.update(observation.id for observation in observations)
    expected_ids.update(immunization.id for immunization in immunizations)

    assert resource_ids == expected_ids

    for entry in summary.entry:
        assert entry.fullUrl.startswith('urn:uuid:')
        assert f'urn:uuid:{entry.resource.id}' == entry.fullUrl
