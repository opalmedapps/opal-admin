# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions related to building an International Patient Summary (IPS) document as a FHIR Bundle."""

import datetime as dt
import uuid

from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _

from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.composition import Composition, CompositionSection
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.device import Device, DeviceDeviceName
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.narrative import Narrative
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.reference import Reference


def build_patient_summary(  # noqa: PLR0913, PLR0917
    patient: Patient,
    conditions: list[Condition],
    medication_requests: list[MedicationRequest],
    allergies: list[AllergyIntolerance],
    observations: list[Observation],
    immunizations: list[Immunization],
) -> Bundle:
    """
    Build an International Patient Summary (IPS) document as a FHIR Bundle.

    Args:
        patient: the Patient resource
        conditions: the list of Condition resources
        medication_requests: the list of MedicationRequest resources
        allergies: the list of AllergyIntolerance resources
        observations: the list of Observation resources
        immunizations: the list of Immunization resources

    Returns:
        the IPS as a FHIR Bundle resource
    """
    vital_signs = [
        observation for observation in observations if observation.category[0].coding[0].code == 'vital-signs'
    ]
    labs = [observation for observation in observations if observation.category[0].coding[0].code == 'laboratory']

    generator = Device(
        id=f'{uuid.uuid4()}',
        language=get_language(),
        manufacturer=_('Opal Health Informatics Group'),
        deviceName=[DeviceDeviceName(name=_('Opal IPS Generator'), type='user-friendly-name')],
    )

    last_updated = timezone.now().astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %H:%M:%S %Z')
    composition = Composition(
        id=f'{uuid.uuid4()}',
        language=get_language(),
        status='final',
        type=CodeableConcept(
            coding=[Coding(system='http://loinc.org', code='60591-5', display='Patient summary Document')],
        ),
        author=[Reference(reference=f'urn:uuid:{generator.id}')],
        date=dt.datetime.now(tz=dt.UTC).replace(microsecond=0),
        title=_('International Patient Summary as of {date}').format(date=last_updated),
        subject=Reference(reference=f'urn:uuid:{patient.id}'),
        section=[
            CompositionSection(
                title=_('Active Problems'),
                code=CodeableConcept(
                    coding=[Coding(system='http://loinc.org', code='11450-4', display='Problem list Reported')]
                ),
                entry=[
                    Reference(reference=f'urn:uuid:{condition.id}')
                    for condition in conditions
                    if condition.clinicalStatus.coding[0].code == 'active'
                ],
            ),
            CompositionSection(
                title=_('Past Medical History'),
                code=CodeableConcept(
                    coding=[Coding(system='http://loinc.org', code='11348-0', display='History of Past illness note')]
                ),
                entry=[
                    Reference(reference=f'urn:uuid:{condition.id}')
                    for condition in conditions
                    if condition.clinicalStatus.coding[0].code != 'active'
                ],
            ),
            CompositionSection(
                title=_('Medication'),
                code=CodeableConcept(
                    coding=[
                        Coding(system='http://loinc.org', code='10160-0', display='History of Medication use Narrative')
                    ],
                ),
                entry=[
                    Reference(reference=f'urn:uuid:{medication_request.id}')
                    for medication_request in medication_requests
                ],
            ),
            CompositionSection(
                title=_('Allergies and Intolerances'),
                code=CodeableConcept(
                    coding=[
                        Coding(
                            system='http://loinc.org',
                            code='48765-2',
                            display='Allergies and adverse reactions Document',
                        )
                    ]
                ),
                entry=[Reference(reference=f'urn:uuid:{allergy.id}') for allergy in allergies],
            ),
            CompositionSection(
                title=_('Vital Signs'),
                code=CodeableConcept(
                    coding=[Coding(system='http://loinc.org', code='8716-3', display='Vital signs note')]
                ),
                entry=[Reference(reference=f'urn:uuid:{vital_sign.id}') for vital_sign in vital_signs],
            ),
            CompositionSection(
                title=_('Laboratory Results'),
                code=CodeableConcept(
                    coding=[
                        Coding(
                            system='http://loinc.org',
                            code='30954-2',
                            display='Relevant diagnostic tests/laboratory data note',
                        )
                    ]
                ),
                entry=[Reference(reference=f'urn:uuid:{lab.id}') for lab in labs],
            ),
            CompositionSection(
                title=_('Immunizations'),
                code=CodeableConcept(
                    coding=[Coding(system='http://loinc.org', code='11369-6', display='History of Immunization note')]
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

    ips.entry.extend(BundleEntry(resource=condition, fullUrl=f'urn:uuid:{condition.id}') for condition in conditions)
    ips.entry.extend(BundleEntry(resource=allergy, fullUrl=f'urn:uuid:{allergy.id}') for allergy in allergies)
    ips.entry.extend(
        BundleEntry(resource=medication_request, fullUrl=f'urn:uuid:{medication_request.id}')
        for medication_request in medication_requests
    )
    ips.entry.extend(
        BundleEntry(resource=vital_sign, fullUrl=f'urn:uuid:{vital_sign.id}') for vital_sign in vital_signs
    )
    ips.entry.extend(BundleEntry(resource=lab, fullUrl=f'urn:uuid:{lab.id}') for lab in labs)
    ips.entry.extend(
        BundleEntry(resource=immunization, fullUrl=f'urn:uuid:{immunization.id}') for immunization in immunizations
    )

    # add narrative for empty entries
    for section in composition.section:
        if not section.entry:
            section.text = Narrative(
                status='generated',
                div=f'<div xmlns="http://www.w3.org/1999/xhtml">{_("There is no information available about the subject's {category}.").format(category=section.title.lower())}</div>',
            )
            section.entry = None

    return ips
