# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module for common validators for `patients` app."""

from collections import Counter

from opal.patients.models import Patient
from opal.services.integration.schemas import PatientSchema


# Patients Validators
def is_deceased(patient: Patient | PatientSchema) -> bool:
    """
    Check if a patient is deceased.

    Args:
        patient: either patient object or patient record from source system

    Returns:
        True if patient is deceased, False otherwise
    """
    return patient.date_of_death is not None


def has_multiple_mrns_with_same_site_code(patient_record: PatientSchema) -> bool:
    """
    Check if the number of MRN records with the same site code is greater than 1.

    Args:
        patient_record: patient record search by RAMQ or MRN

    Returns:
        True if the number of MRN records with the same site code is greater than 1
    """
    mrns = patient_record.mrns
    key_counts = Counter(hospital_number.site for hospital_number in mrns)
    return any(count > 1 for (site, count) in key_counts.items())
