"""Module for common validators for `patients` app."""
from collections import Counter
from typing import Any

from opal.patients.models import Patient
from opal.services.hospital.hospital_data import OIEPatientData


# Patients Validators
def is_valid_patient_record(patient: Patient | OIEPatientData) -> bool:
    """
    Check if patient is valid patient record.

    Args:
        patient: patient object or oie patient record

    Returns:
        True if patient is an object of Patient model or OIEPatientData. False otherwise.

    """
    return isinstance(patient, (Patient, OIEPatientData))


def is_deceased(patient: Patient | OIEPatientData) -> bool:
    """
    Check if a patient is deceased.

    Args:
        patient: either patient object or patient record from OIE

    Returns:
        True if patient is deceased, False otherwise
    """
    if isinstance(patient, Patient):
        if patient.date_of_death:
            return True
    else:
        patient_dict: dict[str, Any] = patient._asdict()  # noqa: WPS437

        if patient_dict.get('deceased'):
            return True

    return False


def has_multiple_mrns_with_same_site_code(patient_record: OIEPatientData) -> bool:
    """
    Check if the number of MRN records with the same site code is greater than 1.

    Args:
        patient_record: patient record search by RAMQ or MRN

    Returns:
        True if the number of MRN records with the same site code is greater than 1
    """
    # TODO: the same function is used in patients/views.py, refactor to reuse.
    if isinstance(patient_record, Patient):
        return False

    mrns = patient_record.mrns
    key_counts = Counter(mrn_dict.site for mrn_dict in mrns)
    return any(count > 1 for (site, count) in key_counts.items())
