import secrets

from jose import jwe, utils

from . import ips
from .fhir import FHIRConnector


# https://docs.smarthealthit.org/smart-health-links/spec/#encrypting-and-decrypting-files
def jwe_sh_link_encrypt(data: str) -> tuple[str, bytes]:
    # generate key with 32 bytes of randomness
    key = secrets.token_urlsafe(32)
    # base64 URL decode to have 32 bytes of data
    key_decoded = utils.base64url_decode(key.encode('utf-8'))

    encrypted = jwe.encrypt(data, key_decoded, algorithm='dir', encryption='A256GCM', cty='application/fhir+json')

    return (key, encrypted)


def build_patient_summary(oauth_url: str, fhir_url: str, client_id: str, private_key: str, identifier: str) -> str:
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

    ips_bundle = ips.build_patient_summary(
        patient, conditions, medication_requests, allergies, observations, immunizations
    )

    return ips_bundle.model_dump_json(indent=2)  # type: ignore[no-any-return]
