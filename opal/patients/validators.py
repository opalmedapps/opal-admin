"""Module for common validators for `patients` app."""
from collections import Counter
from typing import Union

from opal.patients.models import Patient
from opal.services.hospital.hospital_data import OIEPatientData


# Patients Validators
def is_deceased(patient: Union[Patient, OIEPatientData]) -> bool:
    """
    Check if a patient is deceased.

    Args:
        patient: either patient object or patient record from OIE

    Returns:
        True if patient is deceased, False otherwise
    """
    if isinstance(patient, Patient):
        return patient.date_of_death is not None

    return patient.deceased


def has_multiple_mrns_with_same_site_code(patient_record: OIEPatientData) -> bool:
    """
    Check if the number of MRN records with the same site code is greater than 1.

    Args:
        patient_record: patient record search by RAMQ or MRN

    Returns:
        True if the number of MRN records with the same site code is greater than 1
    """
    mrns = patient_record.mrns
    key_counts = Counter(mrn_dict.site for mrn_dict in mrns)
    return any(count > 1 for (site, count) in key_counts.items())
