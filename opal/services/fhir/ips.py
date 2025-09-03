import datetime as dt
import uuid

from django.utils import timezone

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


def build_patient_summary(
    patient: Patient,
    conditions: list[Condition],
    medication_requests: list[MedicationRequest],
    allergies: list[AllergyIntolerance],
    observations: list[Observation],
    immunizations: list[Immunization],
) -> Bundle:
    vital_signs = [
        observation for observation in observations if observation.category[0].coding[0].code == 'vital-signs'
    ]
    labs = [observation for observation in observations if observation.category[0].coding[0].code == 'laboratory']

    generator = Device(
        id=f'{uuid.uuid4()}',
        manufacturer='Opal Health Informatics Group',
        deviceName=[DeviceDeviceName(name='Opal IPS Generator', type='user-friendly-name')],
    )

    last_updated = timezone.now().astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %H:%M:%S %Z')
    composition = Composition(
        id=f'{uuid.uuid4()}',
        status='final',
        type=CodeableConcept(
            coding=[Coding(system='http://loinc.org', code='60591-5', display='Patient summary document')],
        ),
        author=[Reference(reference=f'urn:uuid:{generator.id}')],
        date=dt.datetime.now(tz=dt.UTC).replace(microsecond=0),
        title=f'International Patient Summary as of {last_updated}',
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
                    coding=[
                        Coding(system='http://loinc.org', code='11348-0', display='History of Past illness Narrative')
                    ]
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
                        Coding(system='http://loinc.org', code='10160-0', display='History of Medication use Narrative')
                    ],
                ),
                entry=[
                    Reference(reference=f'urn:uuid:{medication_request.id}')
                    for medication_request in medication_requests
                ],
            ),
            CompositionSection(
                title='Allergies and Intolerances',
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
                title='Vital Signs',
                code=CodeableConcept(coding=[Coding(system='http://loinc.org', code='8716-3', display='Vital signs')]),
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
                    coding=[
                        Coding(system='http://loinc.org', code='11369-6', display='History of Immunization Narrative')
                    ]
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
                div=f'<div xmlns="http://www.w3.org/1999/xhtml">There is no information available about the subject\'s {section.title.lower()}.</div>',
            )
            section.entry = None

    return ips
